"""Fail-closed conversion of gimbal-device attitude into vehicle BODY_FRD."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

YAW_LOCK = 16
YAW_IN_VEHICLE_FRAME = 32
YAW_IN_EARTH_FRAME = 64


@dataclass(frozen=True)
class GimbalAttitude:
    quaternion: tuple[float, float, float, float]
    flags: int
    failure_flags: int
    delta_yaw: float
    component_id: int
    device_id: int
    received_monotonic: float
    time_boot_ms: int


def _rotation_from_quaternion(q) -> np.ndarray:
    q = np.asarray(q, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all():
        raise ValueError("Gimbal quaternion is invalid")
    norm = float(np.linalg.norm(q))
    if not 0.5 <= norm <= 1.5:
        raise ValueError("Gimbal quaternion norm is invalid")
    w, x, y, z = q / norm
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def gimbal_to_body_rotation(sample: GimbalAttitude) -> np.ndarray:
    if sample.failure_flags:
        raise ValueError(f"Gimbal reports failure flags 0x{sample.failure_flags:x}")
    vehicle = bool(sample.flags & YAW_IN_VEHICLE_FRAME)
    earth = bool(sample.flags & YAW_IN_EARTH_FRAME)
    if vehicle and earth:
        raise ValueError("Gimbal reports conflicting yaw-frame flags")
    rotation = _rotation_from_quaternion(sample.quaternion)
    if vehicle or (not earth and not (sample.flags & YAW_LOCK)):
        return rotation
    if not math.isfinite(sample.delta_yaw):
        raise ValueError("Earth-frame gimbal attitude has no usable delta_yaw")
    c, s = math.cos(-sample.delta_yaw), math.sin(-sample.delta_yaw)
    earth_to_vehicle = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    return earth_to_vehicle @ rotation


def target_in_body(
    camera_vector,
    sample: GimbalAttitude,
    camera_to_gimbal,
    max_downward_error_deg: float,
):
    camera_vector = np.asarray(camera_vector, dtype=float)
    camera_to_gimbal = np.asarray(camera_to_gimbal, dtype=float)
    rotation = gimbal_to_body_rotation(sample)
    optical_axis_body = rotation @ camera_to_gimbal @ np.array([0.0, 0.0, 1.0])
    cosine = float(np.clip(optical_axis_body @ np.array([0.0, 0.0, 1.0]), -1, 1))
    downward_error_deg = math.degrees(math.acos(cosine))
    if downward_error_deg > max_downward_error_deg:
        raise ValueError(
            f"Gimbal is {downward_error_deg:.1f} deg from the downward landing envelope"
        )
    return rotation @ camera_to_gimbal @ camera_vector, downward_error_deg
