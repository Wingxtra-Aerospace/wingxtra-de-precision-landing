import importlib
import json
import socket
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pymavlink.dialects.v20 import common as mavlink

from wingxtra_pl.camera import Frame
from wingxtra_pl.config import Config
from wingxtra_pl.service import LandingService
from wingxtra_pl.web import create_app
from conftest import render_board
from test_protocol_tracking import free_port, heartbeat


class FakeCamera:
    def __init__(self, config):
        self.latest, self.error = None, None

    def start(self):
        pass

    def close(self):
        pass

    def snapshot(self):
        return self.latest


def make_service(tmp_path, board_data):
    config = Config()
    config.output.listen_port = free_port()
    (tmp_path / "config.json").write_text(config.model_dump_json())
    (tmp_path / "landing-target.json").write_text(json.dumps(board_data))
    return LandingService(tmp_path, camera_factory=FakeCamera)


def test_real_pipeline_sends_only_new_accepted_frames_and_stops_on_loss(
    tmp_path, board_data, layout, intrinsics, calibration, monkeypatch
):
    service = make_service(tmp_path, board_data)
    service.import_calibration(calibration)
    service._open_link()
    service.control("publish")
    clock = [100.0]
    monkeypatch.setattr(time, "monotonic", lambda: clock[0])
    frame = render_board(layout, intrinsics)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
        router.bind(("127.0.0.1", 0))
        router.settimeout(0.05)
        router.sendto(heartbeat(), service.link.socket.getsockname())
        for seq in range(1, 6):
            clock[0] += 0.06
            service.camera.latest = Frame(frame, seq, clock[0], 1000000 + seq)
            service.tick()
        messages = []
        decoder = mavlink.MAVLink(None)
        try:
            while True:
                messages.extend(decoder.parse_buffer(router.recv(1000)))
        except TimeoutError:
            pass
        assert len(messages) == 3  # First two frames acquire the target.
        assert [m.time_usec for m in messages] == [1000003, 1000004, 1000005]
        assert [messages[-1].x, messages[-1].y, messages[-1].z] == pytest.approx(
            [0.04, 0.05, 1.4], abs=0.02
        )
        sent = service.sent_count
        service.tick()  # Same frame must not be retransmitted.
        clock[0] += 0.4
        service.tick()  # Old frame must not be retransmitted.
        assert service.sent_count == sent
        assert not service.status()["measurement"]["accepted"]
        # A newly decoded image cannot bypass a lost flight-controller heartbeat.
        clock[0] += 4
        for seq in range(6, 10):
            clock[0] += 0.06
            service.camera.latest = Frame(frame, seq, clock[0], 1000000 + seq)
            service.tick()
        assert service.sent_count == sent
        assert "heartbeat" in service.last_measurement["reason"]
        service.control("stopped")
        service.tick()
        assert service.sent_count == sent
    service.close()


def test_api_calibration_required_configuration_lock_and_persistence(
    tmp_path, board_data, calibration
):
    service = make_service(tmp_path, board_data)
    headers = {"X-Wingxtra-Request": "1"}
    with TestClient(create_app(tmp_path, service)) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/register_service").json()["works_in_relative_paths"] is True
        assert client.get("/assets/app.js").status_code == 200
        assert client.post("/api/control", json={"mode": "publish"}).status_code == 403
        assert (
            client.post("/api/control", headers=headers, json={"mode": "publish"}).status_code
            == 409
        )
        assert (
            client.put(
                "/api/calibration", headers=headers, json=calibration.model_dump()
            ).status_code
            == 200
        )
        assert (
            client.post("/api/control", headers=headers, json={"mode": "publish"}).status_code
            == 200
        )
        assert (
            client.put("/api/config", headers=headers, json=service.config.model_dump()).status_code
            == 409
        )
        assert client.put("/api/board", headers=headers, json=board_data).status_code == 409
        assert (
            client.post("/api/control", headers=headers, json={"mode": "stopped"}).status_code
            == 200
        )
        service.link.armed = True
        assert (
            client.put("/api/config", headers=headers, json=service.config.model_dump()).status_code
            == 409
        )
        service.link.armed = False
        changed = service.config.model_dump()
        changed["camera"]["lens_profile"] = "changed-lens"
        assert client.put("/api/config", headers=headers, json=changed).status_code == 200
        assert not client.get("/api/status").json()["calibration"]["valid"]
        assert client.get("/api/board.svg").text.startswith("<svg")
        assert client.get("/api/chessboard.svg?columns=100").status_code == 409
        assert client.get("/api/logs").status_code == 200
    restored = LandingService(tmp_path)
    assert restored.config.camera.lens_profile == "changed-lens"
    assert restored.estimator is None
    restored.close()


def test_api_under_blueos_relative_prefix(tmp_path, board_data):
    service = make_service(tmp_path, board_data)
    service.start()
    parent = FastAPI()
    parent.mount("/extensionv2/wingxtraprecisionlanding", create_app(tmp_path, service))
    try:
        with TestClient(parent) as client:
            base = "/extensionv2/wingxtraprecisionlanding/"
            assert client.get(base).status_code == 200
            assert client.get(base + "assets/style.css").status_code == 200
            assert client.get(base + "api/status").json()["mode"] == "stopped"
    finally:
        service.close()


def test_hardware_optional_modules_import_without_picamera2():
    for name in [
        "wingxtra_pl.main",
        "wingxtra_pl.camera",
        "wingxtra_pl.mavlink_out.databus_internal_mavlink",
    ]:
        assert importlib.import_module(name)


def test_invalid_mount_nan_or_non_live_source_cannot_be_saved():
    for change in [
        {"kind": "v4l2", "source": "/dev/serial0"},
        {"kind": "rtsp", "source": "/tmp/replay.mp4"},
    ]:
        c = Config().model_dump()
        c["camera"].update(change)
        with pytest.raises(ValueError):
            Config.model_validate(c)
