"""Failure cases found in the second review, including the printable board output."""

import copy
import socket
import sys
import time
import xml.etree.ElementTree as ET

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from wingxtra_pl.board_svg import board_svg
from wingxtra_pl.camera import Camera
from wingxtra_pl.config import CameraConfig, OutputConfig
from wingxtra_pl.landing_target_layout import LandingTargetLayout
from wingxtra_pl.mavlink_out.udp import RouterLink
from wingxtra_pl.service import LandingService
from wingxtra_pl.web import create_app
from test_protocol_tracking import free_port, heartbeat
from test_service_web import make_service


@pytest.mark.parametrize(
    "corners",
    [
        3,
        True,
        "1234",
        {"a": 1, "b": 2, "c": 3, "d": 4},
        [{}, {}, {}, {}],
        [[10**400, 0, 0]] * 4,
        [["0", "0", "0"]] * 4,
    ],
)
def test_invalid_corner_json_returns_client_error_without_changing_board(
    tmp_path, board_data, corners
):
    service = make_service(tmp_path, board_data)
    changed = copy.deepcopy(board_data)
    changed["markers"][0]["object_points"] = corners
    with TestClient(create_app(tmp_path, service)) as client:
        response = client.put("/api/board", headers={"X-Wingxtra-Request": "1"}, json=changed)
        assert response.status_code == 409
        assert client.get("/api/board").json() == board_data


def rasterize_export(svg):
    """Paint the exported SVG rectangles/transforms, not the source marker dictionary."""
    root = ET.fromstring(svg)
    x, y, width, height = map(float, root.attrib["viewBox"].split())
    scale = 4.0  # Pixels/mm, sufficient for the smallest original-board tags.
    image = np.full((int(height * scale) + 1, int(width * scale) + 1), 255, np.uint8)

    def paint(node, transform=np.eye(3), inherited="black"):
        transform = transform.copy()
        if "transform" in node.attrib:
            a, b, c, d, e, f = map(float, node.attrib["transform"][7:-1].split())
            transform = transform @ np.array([[a, c, e], [b, d, f], [0, 0, 1]])
        fill = node.attrib.get("fill", inherited)
        if node.tag.endswith("}rect"):
            left, top = float(node.attrib.get("x", 0)), float(node.attrib.get("y", 0))
            w, h = float(node.attrib["width"]), float(node.attrib["height"])
            points = (
                np.array(
                    [[left, top, 1], [left + w, top, 1], [left + w, top + h, 1], [left, top + h, 1]]
                )
                @ transform.T
            )
            pixels = np.round((points[:, :2] - [x, y]) * scale).astype(np.int32)
            cv2.fillConvexPoly(image, pixels, 255 if fill == "white" else 0)
        for child in node:
            paint(child, transform, fill)

    paint(root)
    return image


@pytest.mark.parametrize("original", [False, True])
def test_exported_svg_tags_decode_for_both_board_axis_conventions(
    layout, original_layout, original
):
    chosen = original_layout if original else layout
    image = rasterize_export(board_svg(chosen))
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    if hasattr(cv2.aruco, "ArucoDetector"):
        _, ids, _ = cv2.aruco.ArucoDetector(dictionary).detectMarkers(image)
    else:
        _, ids, _ = cv2.aruco.detectMarkers(image, dictionary)
    assert ids is not None
    assert set(ids.flatten()) == set(chosen.markers)


def test_mixed_corner_winding_is_rejected(board_data):
    changed = copy.deepcopy(board_data)
    changed["markers"][0]["object_points"].reverse()
    with pytest.raises(ValueError, match="winding"):
        LandingTargetLayout.from_dict(changed)


def test_buffered_heartbeat_does_not_become_fresh_when_read_late(monkeypatch):
    link = RouterLink(OutputConfig(listen_port=free_port(), heartbeat_timeout_s=1))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
            router.sendto(heartbeat(), link.socket.getsockname())
            wall_ns = time.time_ns
            # Simulate delayed application receive without a slow test sleep.
            monkeypatch.setattr(time, "time_ns", lambda: wall_ns() + 2_000_000_000)
            link.poll()
            assert not link.fresh()
            assert not link.send(b"must not send")
            monkeypatch.setattr(time, "time_ns", wall_ns)
            router.sendto(heartbeat(armed=True), link.socket.getsockname())
            link.poll()
            assert link.fresh() and link.armed is True
    finally:
        link.close()


def test_undrained_telemetry_backlog_blocks_output():
    link = RouterLink(OutputConfig(listen_port=free_port()))
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
            router.sendto(heartbeat(), link.socket.getsockname())
            for _ in range(65):
                router.sendto(b"junk", link.socket.getsockname())
            router.sendto(heartbeat(armed=True), link.socket.getsockname())
            link.poll()
            assert not link.fresh()
            link.poll()
            assert link.fresh() and link.armed is True
    finally:
        link.close()


def test_setup_reads_pending_armed_heartbeat_before_editing(tmp_path, board_data):
    service = make_service(tmp_path, board_data)
    service._open_link()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
            router.sendto(heartbeat(armed=True), service.link.socket.getsockname())
            with pytest.raises(ValueError, match="armed"):
                service.update_board(board_data)
    finally:
        service.close()


def test_expired_disarmed_state_does_not_unlock_setup(tmp_path, board_data):
    service = make_service(tmp_path, board_data)
    service._open_link()
    try:
        service.link.armed = False
        service.link.last_heartbeat = time.monotonic() - 10
        with pytest.raises(ValueError, match="fresh disarmed heartbeat"):
            service.update_board(board_data)
    finally:
        service.close()


def test_config_rechecks_arming_after_camera_shutdown(tmp_path, board_data):
    service = make_service(tmp_path, board_data)
    service._open_link()
    service.control("monitor")
    original = service.config.model_dump()
    changed = service.config.model_copy(deep=True)
    changed.camera.lens_profile = "must-not-save"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
            service.camera.close = lambda: router.sendto(
                heartbeat(armed=True), service.link.socket.getsockname()
            )
            with pytest.raises(ValueError, match="armed"):
                service.update_config(changed)
            assert service.config.model_dump() == original
            assert service.mode == "stopped"
    finally:
        service.close()


def test_calibration_solve_rechecks_arming_before_persisting(tmp_path, board_data, calibration):
    service = make_service(tmp_path, board_data)
    service._open_link()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:

            class SolveWhileArming:
                def solve(self):
                    router.sendto(heartbeat(armed=True), service.link.socket.getsockname())
                    return calibration

            service.session = SolveWhileArming()
            with pytest.raises(ValueError, match="armed"):
                service.calibration_solve()
            assert not (tmp_path / "camera.json").exists()
    finally:
        service.close()


def test_databus_startup_failure_closes_listener_and_blocks_publish(
    tmp_path, board_data, calibration, monkeypatch
):
    service = make_service(tmp_path, board_data)
    service.import_calibration(calibration)
    service.config.output.mode = "droneengage_databus"

    def failed_databus(*args, **kwargs):
        raise OSError("injected unavailable transport")

    monkeypatch.setattr("wingxtra_pl.service.DroneEngageDatabusInternalMavlinkOut", failed_databus)
    try:
        service._open_link()
        assert service.link is None and service.databus is None
        with pytest.raises(ValueError, match="endpoint"):
            service.control("publish")
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.bind(("127.0.0.1", service.config.output.listen_port))
    finally:
        service.close()


def test_failed_camera_shutdown_requires_restart_and_still_closes_outputs(
    tmp_path, board_data, calibration
):
    service = make_service(tmp_path, board_data)
    service.import_calibration(calibration)
    service._open_link()
    service.control("monitor")
    camera = service.camera
    link = service.link

    def stuck_close():
        raise RuntimeError("injected driver timeout")

    camera.close = stuck_close
    with pytest.raises(ValueError, match="restart"):
        service.control("stopped")
    assert service.mode == "stopped"
    assert not service.status()["camera"]["connected"]
    for mode in ["monitor", "publish"]:
        with pytest.raises(ValueError, match="restart"):
            service.control(mode)
    service.close()
    assert link.socket.fileno() == -1


def test_camera_driver_cleanup_error_is_reported_and_clears_image(monkeypatch):
    class BadCapture:
        def isOpened(self):
            return True

        def read(self):
            return False, None

        def release(self):
            raise OSError("injected cleanup failure")

    monkeypatch.setattr(cv2, "VideoCapture", lambda *args: BadCapture())
    camera = Camera(CameraConfig())
    camera.start()
    camera.thread.join(timeout=1)
    assert not camera.thread.is_alive()
    assert camera.snapshot() is None
    assert "restart" in camera.error
    with pytest.raises(RuntimeError, match="restart"):
        camera.close()


def test_preview_api_does_not_return_expired_image(tmp_path, board_data):
    service = make_service(tmp_path, board_data)
    with TestClient(create_app(tmp_path, service)) as client:
        service.control("monitor")
        with service.lock:
            service.last_preview = b"expired jpeg"
            service.last_preview_time = time.monotonic() - 1
        assert client.get("/api/preview.jpg").status_code == 404


@pytest.mark.parametrize(
    "arguments,environment",
    [
        (["--databus-port", "0"], {}),
        (["--databus-host", ""], {}),
        ([], {"DATABUS_PORT": ""}),
        ([], {"DATABUS_HOST": ""}),
    ],
)
def test_invalid_explicit_databus_override_is_not_silently_ignored(
    tmp_path, monkeypatch, arguments, environment
):
    from wingxtra_pl import main

    services = []

    def make(data):
        service = LandingService(data)
        services.append(service)
        return service

    def must_not_start(*args, **kwargs):
        pytest.fail("Invalid explicit override reached server startup")

    monkeypatch.delenv("DATABUS_HOST", raising=False)
    monkeypatch.delenv("DATABUS_PORT", raising=False)
    for key, value in environment.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(sys, "argv", ["wingxtra-pl", "--data-dir", str(tmp_path), *arguments])
    monkeypatch.setattr(main, "LandingService", make)
    monkeypatch.setattr(main.uvicorn, "run", must_not_start)
    try:
        with pytest.raises(ValueError, match="DataBus"):
            main.main()
    finally:
        for service in services:
            service.close()
