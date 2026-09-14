"""Exercise actual MAVLink decoding and service rejection, including cached telemetry."""

import math
import socket
from types import SimpleNamespace

import numpy as np
import pytest
from pymavlink.dialects.v20 import common as mavlink
from pymavlink.quaternion import Quaternion

from wingxtra_pl.config import OutputConfig
from wingxtra_pl.gimbal import YAW_IN_VEHICLE_FRAME
from wingxtra_pl.mavlink_out.udp import LandingTargetEncoder, RouterLink
from wingxtra_pl.service import LandingService
from test_protocol_tracking import free_port, heartbeat


def packet(message, *, system=1, component=1):
    return message.pack(mavlink.MAVLink(None, srcSystem=system, srcComponent=component))


def gimbal(stamp, *, component=154, device=1, system=1, failure=0, q=None):
    half = math.sqrt(0.5)
    return packet(
        mavlink.MAVLink_gimbal_device_attitude_status_message(
            0,
            0,
            stamp,
            YAW_IN_VEHICLE_FRAME,
            (half, 0, -half, 0) if q is None else q,
            0,
            0,
            0,
            failure,
            gimbal_device_id=device,
        ),
        system=system,
        component=component,
    )


def aircraft(stamp, *, roll=0, pitch=0, yaw=0, euler=False, component=1, system=1, q=None):
    message = (
        mavlink.MAVLink_attitude_message(stamp, roll, pitch, yaw, 0, 0, 0)
        if euler
        else mavlink.MAVLink_attitude_quaternion_message(
            stamp, *(Quaternion([roll, pitch, yaw]).q if q is None else q), 0, 0, 0
        )
    )
    return packet(message, system=system, component=component)


@pytest.fixture
def telemetry(tmp_path):
    link = RouterLink(OutputConfig(listen_port=free_port()))
    service = LandingService(tmp_path)
    service.config.camera.mode = "gimbal"
    service.config.gimbal.component_id = 154
    service.config.gimbal.device_id = 1
    service.config.gimbal.max_downward_error_deg = 45
    service.link = link
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:

        def feed(now, *packets):
            for data in packets:
                router.sendto(data, link.socket.getsockname())
            link.poll(now=now)

        def target(now, frame_time=None):
            return service._body_from_pose(
                {"tvec": np.array([0.0, 0.0, 2.0])},
                SimpleNamespace(monotonic=now if frame_time is None else frame_time),
                now,
            )

        try:
            yield SimpleNamespace(link=link, service=service, feed=feed, target=target)
        finally:
            service.close()


def prime(t, stamp=1000, **attitude):
    t.feed(10, heartbeat(), gimbal(stamp), aircraft(stamp, **attitude))
    t.feed(10.02, gimbal((stamp + 20) % 2**32), aircraft((stamp + 20) % 2**32, **attitude))


@pytest.mark.parametrize("euler", [False, True])
def test_wire_aircraft_attitude_rotates_gimbal_target_before_encoding(telemetry, euler):
    t = telemetry
    prime(t, roll=math.radians(10), euler=euler)
    body, reason = t.target(10.03)
    assert reason is None
    expected = [0, 2 * math.sin(math.radians(10)), 2 * math.cos(math.radians(10))]
    assert body == pytest.approx(expected, abs=1e-6)
    decoded = mavlink.MAVLink(None).parse_buffer(LandingTargetEncoder().encode(body, 1000))[0]
    assert [decoded.x, decoded.y, decoded.z] == pytest.approx(expected, abs=1e-6)
    assert decoded.frame == mavlink.MAV_FRAME_BODY_FRD and decoded.position_valid == 1


def test_first_or_repeated_startup_timestamp_cannot_authorise_output(telemetry):
    t = telemetry
    t.feed(10, heartbeat(), gimbal(1000), aircraft(1000))
    t.feed(10.02, gimbal(1000), aircraft(1000))
    assert t.target(10.03)[0] is None
    assert not t.link.gimbal_attitudes and not t.link.vehicle_attitudes
    t.feed(10.04, gimbal(1040), aircraft(1040))
    assert t.target(10.05)[1] is None


@pytest.mark.parametrize("frozen", ["gimbal", "aircraft"])
def test_repeated_device_time_expires_despite_fresh_packets_and_heartbeat(telemetry, frozen):
    t = telemetry
    prime(t)
    assert t.target(10.03)[1] is None
    t.feed(
        10.8,
        heartbeat(),
        gimbal(1020 if frozen == "gimbal" else 1800),
        aircraft(1020 if frozen == "aircraft" else 1800),
    )
    body, reason = t.target(10.81)
    assert body is None and ("not aligned" in reason or "stale" in reason)
    history = t.link.gimbal_attitudes if frozen == "gimbal" else t.link.vehicle_attitudes
    assert history[-1].time_boot_ms == 1020
    assert history[-1].received_monotonic < 10.03
    assert t.link.fresh(10.81)


def test_reordered_device_times_do_not_replace_newer_attitude_or_renew_its_age(telemetry):
    t = telemetry
    prime(t)
    original = t.link.gimbal_attitudes[-1]
    t.feed(10.04, gimbal(1010), aircraft(1040))
    assert t.link.gimbal_attitudes[-1] == original
    t.feed(10.06, gimbal(1060), aircraft(1060))
    assert t.target(10.07)[1] is None


def test_uint32_wrap_accepts_forward_progress_and_rejects_old_pre_wrap_packets(telemetry):
    t = telemetry
    prime(t, stamp=2**32 - 10)
    assert t.link.gimbal_attitudes[-1].time_boot_ms == 10
    assert t.target(10.03)[1] is None
    original = t.link.gimbal_attitudes[-1]
    t.feed(10.04, gimbal(2**32 - 5), aircraft(2**32 - 5))
    assert t.link.gimbal_attitudes[-1] == original
    t.feed(10.06, gimbal(50), aircraft(50))
    assert t.target(10.07)[1] is None


@pytest.mark.parametrize("uptime", [100000, 3000000000])
def test_reboot_does_not_rebase_device_clock_even_after_half_the_counter_range(telemetry, uptime):
    t = telemetry
    prime(t, stamp=uptime)
    assert t.target(10.03)[1] is None
    t.feed(10.8, heartbeat(), gimbal(0), aircraft(0))
    t.feed(10.82, gimbal(20), aircraft(20))
    assert t.target(10.83)[0] is None
    assert t.link.gimbal_attitudes[-1].time_boot_ms == uptime + 20
    assert t.link.vehicle_attitudes[-1].time_boot_ms == uptime + 20


@pytest.mark.parametrize("system,component", [(2, 1), (1, 193)])
def test_aircraft_attitude_must_come_from_selected_autopilot(telemetry, system, component):
    t = telemetry
    t.feed(10, heartbeat(), gimbal(1000), aircraft(1000, system=system, component=component))
    t.feed(10.02, gimbal(1020), aircraft(1020, system=system, component=component))
    body, reason = t.target(10.03)
    assert body is None and "aircraft attitude" in reason


def test_device_clocks_are_independent_and_ambiguous_wildcards_are_rejected(telemetry):
    t = telemetry
    prime(t)
    t.feed(10.04, gimbal(0, component=155), aircraft(1040))
    t.feed(10.06, gimbal(20, component=155), aircraft(1060))
    assert t.link.gimbal_clocks[(154, 1)].time_boot_ms == 1020
    assert t.target(10.07)[1] is None  # Explicitly selected device's earlier sample is still fresh.
    t.service.config.gimbal.component_id = 0
    assert "Multiple gimbals" in t.target(10.07)[1]
    t.service.config.gimbal.component_id = 154
    t.feed(10.8, gimbal(760, component=155), aircraft(1800))
    assert t.target(10.81)[0] is None  # Other device cannot refresh the selected one.


@pytest.mark.parametrize("invalid", ["gimbal", "aircraft", "failure"])
def test_new_invalid_feedback_cannot_fall_back_to_nearer_healthy_history(telemetry, invalid):
    t = telemetry
    prime(t)
    t.feed(
        10.04,
        gimbal(
            1040,
            q=(math.nan, 0, 0, 0) if invalid == "gimbal" else None,
            failure=8 if invalid == "failure" else 0,
        ),
        aircraft(1040, q=(0, 0, 0, 0) if invalid == "aircraft" else None),
    )
    assert t.target(10.05, frame_time=10.02)[0] is None


def test_frame_and_attitude_pair_must_both_fit_configured_skew(telemetry):
    t = telemetry
    t.feed(10, heartbeat(), gimbal(1000), aircraft(1000))
    t.feed(10.01, gimbal(1010))
    t.feed(10.27, aircraft(1270))
    # Both are within 0.15 s of the frame, but 0.26 s apart from each other.
    body, reason = t.target(10.28, frame_time=10.14)
    assert body is None and "attitudes are not aligned" in reason


def test_fixed_mode_does_not_require_either_attitude_stream(telemetry):
    t = telemetry
    t.service.config.camera.mode = "fixed"
    t.service.link = None
    body, reason = t.target(10)
    assert reason is None and body == pytest.approx([0, 0, 2])
    t.link.close()


def test_router_peer_change_discards_old_attitude_and_requires_new_clock_progress(telemetry):
    t = telemetry
    prime(t)
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as router:
        for data in (heartbeat(), gimbal(0), aircraft(0)):
            router.sendto(data, t.link.socket.getsockname())
        t.link.poll(now=14)  # Old peer's heartbeat has expired.
        assert t.link.fresh(14)
        assert t.target(14.01)[0] is None
        for data in (gimbal(20), aircraft(20)):
            router.sendto(data, t.link.socket.getsockname())
        t.link.poll(now=14.02)
        assert t.target(14.03)[1] is None
