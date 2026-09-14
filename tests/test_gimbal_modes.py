import math
from pathlib import Path

import pytest

from wingxtra_pl.camera_profiles import camera_profiles
from wingxtra_pl.config import Config
from wingxtra_pl.gimbal import (
    GimbalAttitude,
    YAW_IN_EARTH_FRAME,
    YAW_IN_VEHICLE_FRAME,
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
    )
    assert body == pytest.approx([0, 0, 2], abs=1e-8)
    assert error == pytest.approx(0, abs=1e-6)


def test_earth_frame_status_uses_delta_yaw_to_recover_vehicle_frame():
    # q_earth = yaw(+90) * q_vehicle; delta_yaw allows the inverse conversion.
    q_earth = (0.5, 0.5, -0.5, 0.5)
    body, error = target_in_body(
        [0, 0, 2],
        sample(q=q_earth, flags=YAW_IN_EARTH_FRAME, delta_yaw=math.pi / 2),
        CAMERA_TO_GIMBAL,
        10,
    )
    assert body == pytest.approx([0, 0, 2], abs=1e-8)
    assert error == pytest.approx(0, abs=1e-6)


@pytest.mark.parametrize(
    "attitude, message",
    [
        (sample(q=(1, 0, 0, 0)), "downward"),
        (sample(q=(1, 0, 0, 0), failure_flags=8), "failure"),
        (
            sample(q=(1, 0, 0, 0), flags=YAW_IN_EARTH_FRAME),
            "delta_yaw",
        ),
    ],
)
def test_gimbal_geometry_fails_closed(attitude, message):
    with pytest.raises(ValueError, match=message):
        target_in_body([0, 0, 2], attitude, CAMERA_TO_GIMBAL, 10)


def test_wingxtra_applet_checks_distance_before_navigation_update():
    source = Path("applets/wingxtra_plane_precland.lua").read_text()
    gate = source.index("distance_cutoff > 0 and horizontal_distance > distance_cutoff")
    update = source.index("vehicle:update_target_location(next_wp, new_wp)")
    assert gate < update
    assert "WXPL_CAM_MODE" in source
    assert "if WXPL_CAM_MODE:get() < 1 then" in source
    assert "mount:set_angle_target" in source
    assert "9456449a442617b2af1c3132b64c3120f1694583" in source
