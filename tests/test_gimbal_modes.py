import math
from pathlib import Path

import pytest
import numpy as np
from pymavlink.quaternion import QuaternionBase as Quaternion

from wingxtra_pl.camera_profiles import camera_profiles
from wingxtra_pl.config import Config
from wingxtra_pl.gimbal import (
    GimbalAttitude,
    YAW_LOCK,
    YAW_IN_EARTH_FRAME,
    YAW_IN_VEHICLE_FRAME,
    gimbal_to_body_rotation,
    target_in_body,
)


CAMERA_TO_GIMBAL = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]


def sample(*, q, flags=YAW_IN_VEHICLE_FRAME, failure_flags=0, delta_yaw=math.nan):
    return GimbalAttitude(
        quaternion=q,
        flags=flags,
        failure_flags=failure_flags,
        delta_yaw=delta_yaw,
        component_id=154,
        device_id=1,
        received_monotonic=10.0,
        time_boot_ms=1234,
    )


def test_fixed_and_gimbal_modes_preserve_intrinsic_calibration_identity():
    fixed = Config()
    gimbal = Config.model_validate(fixed.model_dump())
    gimbal.camera.mode = "gimbal"
    gimbal.camera.profile = "siyi-a8"
    assert fixed.camera.fingerprint() == gimbal.camera.fingerprint()


def test_camera_profiles_are_connection_presets_not_calibration_data():
    profiles = camera_profiles()
    assert {"custom", "siyi-a8", "siyi-zr10", "siyi-zt6-rgb", "siyi-zt6-ir"} <= set(profiles)
    assert profiles["siyi-a8"]["recommended_mode"] == "gimbal"
    assert "camera_matrix" not in profiles["siyi-a8"]


def test_downward_vehicle_frame_gimbal_rotates_camera_vector_to_body_down():
    half = math.sqrt(0.5)
    body, error = target_in_body(
        [0, 0, 2],
        sample(q=(half, 0, -half, 0)),
        CAMERA_TO_GIMBAL,
        10,
        vehicle_quaternion=(1, 0, 0, 0),
    )
    assert body == pytest.approx([0, 0, 2], abs=1e-8)
    assert error == pytest.approx(0, abs=1e-6)


def test_earth_frame_status_uses_full_aircraft_attitude_without_delta_yaw():
    q_earth = (0.5, 0.5, -0.5, 0.5)
    body, error = target_in_body(
        [0, 0, 2],
        sample(q=q_earth, flags=YAW_IN_EARTH_FRAME),
        CAMERA_TO_GIMBAL,
        10,
        vehicle_quaternion=Quaternion([0, 0, math.pi / 2]).q,
    )
    assert body == pytest.approx([0, 0, 2], abs=1e-8)
    assert error == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize(
    "attitude, message",
    [
        (sample(q=(1, 0, 0, 0)), "downward"),
        (sample(q=(1, 0, 0, 0), failure_flags=8), "failure"),
        (
            sample(q=(1, 0, 0, 0), flags=YAW_IN_EARTH_FRAME | YAW_IN_VEHICLE_FRAME),
            "conflicting",
        ),
    ],
)
def test_gimbal_geometry_fails_closed(attitude, message):
    with pytest.raises(ValueError, match=message):
        target_in_body([0, 0, 2], attitude, CAMERA_TO_GIMBAL, 10, vehicle_quaternion=(1, 0, 0, 0))


@pytest.mark.parametrize("flags", [YAW_IN_VEHICLE_FRAME, YAW_IN_EARTH_FRAME, 0, YAW_LOCK])
@pytest.mark.parametrize("rpy", [(10, 0, 0), (0, -20, 90), (18, -12, -65)])
@pytest.mark.parametrize("sign", [1, -1])
def test_tilted_aircraft_and_off_axis_target_match_independent_ned_geometry(flags, rpy, sign):
    roll, pitch, yaw = map(math.radians, rpy)
    aircraft = Quaternion([roll, pitch, yaw])
    gimbal_yaw = math.radians(20)
    attitude = sample(
        q=tuple(sign * value for value in Quaternion([0, -math.pi / 2, gimbal_yaw]).q),
        flags=flags,
        # Legacy reports must ignore this; neither path needs it with aircraft attitude.
        delta_yaw=2.7,
    )
    absolute_yaw = gimbal_yaw + (yaw if flags in (0, YAW_IN_VEHICLE_FRAME) else 0)
    # A nadir camera maps camera right -> gimbal right and camera down -> aft.
    target_ned = Quaternion([0, 0, absolute_yaw]).dcm @ np.array([0.2, 0.3, 2])
    expected_body = aircraft.dcm.T @ target_ned
    body, error = target_in_body(
        [0.3, -0.2, 2], attitude, CAMERA_TO_GIMBAL, 45, vehicle_quaternion=aircraft.q
    )
    assert body == pytest.approx(expected_body, abs=1e-6)
    assert np.linalg.norm(body) == pytest.approx(np.linalg.norm(target_ned))
    assert error == pytest.approx(math.degrees(math.acos(math.cos(roll) * math.cos(pitch))))


@pytest.mark.parametrize("q", [(0, 0, 0, 0), (math.nan, 0, 0, 0), (1, 2, 3), None])
def test_missing_or_invalid_aircraft_attitude_is_not_assumed_level(q):
    half = math.sqrt(0.5)
    with pytest.raises(ValueError, match="Aircraft"):
        target_in_body(
            [0, 0, 2],
            sample(q=(half, 0, -half, 0)),
            CAMERA_TO_GIMBAL,
            45,
            vehicle_quaternion=q,
        )


def test_vehicle_heading_singularity_fails_closed():
    with pytest.raises(ValueError, match="heading is undefined"):
        gimbal_to_body_rotation(sample(q=(1, 0, 0, 0)), Quaternion([0, math.pi / 2, 0]).q)


def test_existing_body_down_envelope_is_preserved_for_tilted_aircraft():
    half = math.sqrt(0.5)
    with pytest.raises(ValueError, match="downward landing envelope"):
        target_in_body(
            [0, 0, 2],
            sample(q=(half, 0, -half, 0)),
            CAMERA_TO_GIMBAL,
            10,
            vehicle_quaternion=Quaternion([math.radians(20), 0, 0]).q,
        )


def test_wingxtra_applet_checks_distance_before_navigation_update():
    source = Path("applets/wingxtra_plane_precland.lua").read_text()
    gate = source.index("distance_cutoff > 0 and horizontal_distance > distance_cutoff")
    update = source.index("vehicle:update_target_location(next_wp, new_wp)")
    assert gate < update
    assert "WXPL_CAM_MODE" in source
    assert "if WXPL_CAM_MODE:get() < 1 then" in source
    assert "mount:set_angle_target" in source
    assert "9456449a442617b2af1c3132b64c3120f1694583" in source
