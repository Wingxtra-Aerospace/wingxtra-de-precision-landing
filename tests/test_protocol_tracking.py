import json
import socket

import numpy as np
import pytest
from pymavlink.dialects.v20 import common as mavlink

from wingxtra_pl.config import MountConfig, OutputConfig, QualityConfig
from wingxtra_pl.mavlink_out.databus_internal_mavlink import DroneEngageDatabusInternalMavlinkOut
from wingxtra_pl.mavlink_out.udp import LandingTargetEncoder, RouterLink
from wingxtra_pl.tracking import TargetTracker
from wingxtra_pl.transforms import camera_to_body_ned_default


def test_packet_decodes_required_ardupilot_fields_and_advances_sequence():
    e = LandingTargetEncoder(7, 193)
    decoder = mavlink.MAVLink(None)
    for i in range(260):
        packet = e.encode([0.3, -0.4, 2], 123456789 + i, 4)
        assert packet[0] == 0xFD
        m = decoder.parse_buffer(packet)[0]
        assert m.get_seq() == i % 256
        assert m.get_srcSystem() == 7 and m.get_srcComponent() == 193
        assert m.frame == mavlink.MAV_FRAME_BODY_FRD
        assert m.position_valid == 1 and m.type == mavlink.LANDING_TARGET_TYPE_VISION_FIDUCIAL
        assert m.distance == pytest.approx(np.linalg.norm([0.3, -0.4, 2]))
        assert [m.x, m.y, m.z] == pytest.approx([0.3, -0.4, 2])
        assert m.time_usec == 123456789 + i and m.target_num == 4
        assert m.q == [1, 0, 0, 0]


def test_default_downward_axes():
    # Target at image top must be forward; image right must be body right.
    assert camera_to_body_ned_default(np.array([0.2, -0.3, 2])).tolist() == [0.3, 0.2, 2]
    assert (np.array(MountConfig().camera_to_body) @ [0.2, -0.3, 2]).tolist() == [0.3, 0.2, 2]
    with pytest.raises(ValueError):
        MountConfig(camera_to_body=[[1, 0, 0], [0, -1, 0], [0, 0, 1]])


def heartbeat(system=1, component=1, armed=False, autopilot=mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA):
    e = mavlink.MAVLink(None, srcSystem=system, srcComponent=component)
    m = mavlink.MAVLink_heartbeat_message(
        mavlink.MAV_TYPE_QUADROTOR,
        autopilot,
        mavlink.MAV_MODE_FLAG_SAFETY_ARMED if armed else 0,
        0,
        mavlink.MAV_STATE_STANDBY,
        3,
    )
    return m.pack(e)


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_udp_heartbeat_source_expiry_and_armed_latch():
    link = RouterLink(OutputConfig(listen_port=free_port(), heartbeat_timeout_s=1))
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
        router.bind(("127.0.0.1", 0))
        router.settimeout(0.2)
        destination = link.socket.getsockname()
        assert not link.send(b"test", now=1)
        for invalid in [
            heartbeat(system=2),
            heartbeat(component=193),
            heartbeat(autopilot=8),
            b"junk",
        ]:
            router.sendto(invalid, destination)
            link.poll(now=1)
            assert not link.fresh(now=1)
        router.sendto(heartbeat(armed=True), destination)
        link.poll(now=2)
        assert link.fresh(now=2) and link.armed is True
        packet = LandingTargetEncoder().encode([0, 0, 2], 1000)
        assert link.send(packet, now=2.5)
        assert router.recv(500) == packet
        assert not link.send(packet, now=3.01)
        assert link.armed is True  # Link loss must not unlock configuration.
        router.sendto(heartbeat(armed=False), destination)
        link.poll(now=4)
        assert link.armed is False
    link.close()


def test_udp_port_conflict_fails_instead_of_sharing_socket():
    config = OutputConfig(listen_port=free_port())
    link = RouterLink(config)
    try:
        with pytest.raises(OSError):
            RouterLink(config)
    finally:
        link.close()


def test_databus_actual_wire_prefix_envelope_and_packet():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(0.5)
        out = DroneEngageDatabusInternalMavlinkOut(*receiver.getsockname())
        packet = LandingTargetEncoder().encode([0, 0, 2], 100)
        out.send_landing_target(packet)
        registration = receiver.recv(2048)
        assert registration[:2] == b"\xff\xff"
        reg = json.loads(registration[2:])
        assert reg["mt"] == 9100 and reg["ms"]["b"] == "gen"
        data = receiver.recv(2048)
        assert data[:2] == b"\xff\xff"
        header, binary = data[2:].split(b"\0", 1)
        assert json.loads(header) == {
            "GU": "wingxtra-precision-landing",
            "tg": "",
            "ty": "uv",
            "mt": 6504,
            "ms": {},
        }
        assert binary == packet
        out.close()


def test_no_duplicate_stale_or_rejected_measurement_retransmission():
    q = QualityConfig()
    t = TargetTracker(q)
    p = {"num_markers_used": 3, "reproj_rmse_px": 0.3}
    assert not t.accept(p, [0, 0, 2], 1, 1.01, 1)
    assert not t.accept(p, [0, 0, 2], 1.05, 1.06, 2)
    assert t.accept(p, [0, 0, 2], 1.1, 1.11, 3)
    assert not t.accept(p, [0, 0, 2], 1.1, 1.12, 3)
    assert not t.accept(p, [0, 0, 2], 1.15, 1.5, 4)
    assert not t.accept({**p, "reproj_rmse_px": 8}, [0, 0, 2], 1.55, 1.56, 5)
    assert t.last_time == 1.1
    assert not t.accept(p, [10, 0, 2], 1.6, 1.61, 6)


def test_target_reacquisition_resets_after_loss_and_rejects_bad_vectors():
    t = TargetTracker(QualityConfig())
    p = {"num_markers_used": 2, "reproj_rmse_px": 0.2}
    for i in range(3):
        result = t.accept(p, [0, 0, 2], 1 + i * 0.05, 1 + i * 0.05, i)
    assert result
    assert not t.accept(None, None, 1.2, 1.2, 3)
    assert not t.accept(p, [5, 0, 2], 2, 2, 4)
    assert not t.accept(p, [5, 0, 2], 2.05, 2.05, 5)
    assert t.accept(p, [5, 0, 2], 2.1, 2.1, 6)
    for i, body in enumerate([[0, 0, -2], [float("nan"), 0, 2], [0, 0, 0]]):
        assert not t.accept(p, body, 3 + i * 0.05, 3 + i * 0.05, 7 + i)
