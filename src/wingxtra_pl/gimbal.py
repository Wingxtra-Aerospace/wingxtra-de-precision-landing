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


@dataclass(frozen=True)
class VehicleAttitude:
    quaternion: tuple[float, float, float, float]
    received_monotonic: float
    time_boot_ms: int


def quaternion_from_euler(roll: float, pitch: float, yaw: float):
    """MAVLink ATTITUDE's intrinsic ZYX angles, BODY_FRD -> NED."""
    if not all(math.isfinite(angle) for angle in (roll, pitch, yaw)):
        raise ValueError("Aircraft attitude is invalid")
    cr, sr = math.cos(roll / 2), math.sin(roll / 2)
    cp, sp = math.cos(pitch / 2), math.sin(pitch / 2)
    cy, sy = math.cos(yaw / 2), math.sin(yaw / 2)
    return (
        cr * cp * cy + sr * sp * sy,
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
    )


def rotation_from_quaternion(q, name="Gimbal") -> np.ndarray:
    q = np.asarray(q, dtype=float)
    if q.shape != (4,) or not np.isfinite(q).all():
        raise ValueError(f"{name} quaternion is invalid")
    norm = float(np.linalg.norm(q))
    if not 0.5 <= norm <= 1.5:
        raise ValueError(f"{name} quaternion norm is invalid")
    w, x, y, z = q / norm
    return np.array(
        [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]
    )


def gimbal_reference_rotation(sample: GimbalAttitude) -> np.ndarray:
    if sample.failure_flags:
        raise ValueError(f"Gimbal reports failure flags 0x{sample.failure_flags:x}")
    vehicle = bool(sample.flags & YAW_IN_VEHICLE_FRAME)
    earth = bool(sample.flags & YAW_IN_EARTH_FRAME)
    if vehicle and earth:
        raise ValueError("Gimbal reports conflicting yaw-frame flags")
    return rotation_from_quaternion(sample.quaternion)


def gimbal_to_body_rotation(sample: GimbalAttitude, vehicle_quaternion) -> np.ndarray:
    """Convert the reported horizon/heading frame, never assume it is BODY_FRD."""
    rotation = gimbal_reference_rotation(sample)
    body_to_earth = rotation_from_quaternion(vehicle_quaternion, "Aircraft")
    vehicle = bool(sample.flags & YAW_IN_VEHICLE_FRAME)
    earth = bool(sample.flags & YAW_IN_EARTH_FRAME)
    if vehicle or (not earth and not (sample.flags & YAW_LOCK)):
        # MAVLink's 'vehicle frame' is level with the horizon, rotated only in yaw.
        # Recover heading from the measured aircraft attitude, then undo all three
        # aircraft axes. A vertical aircraft nose has no defined heading.
        north, east = body_to_earth[:2, 0]
        horizontal = math.hypot(north, east)
        if horizontal < 1e-6:
            raise ValueError("Aircraft heading is undefined for vehicle-frame gimbal attitude")
        c, s = north / horizontal, east / horizontal
        heading_to_earth = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        rotation = heading_to_earth @ rotation
    # Earth-frame reports already contain absolute yaw. delta_yaw is unnecessary
    # here, and MAVLink requires ignoring it when the explicit frame flags are absent.
    return body_to_earth.T @ rotation


def target_in_body(
    camera_vector,
    sample: GimbalAttitude,
    camera_to_gimbal,
    max_downward_error_deg: float,
    *,
    vehicle_quaternion,
):
    camera_vector = np.asarray(camera_vector, dtype=float)
    camera_to_gimbal = np.asarray(camera_to_gimbal, dtype=float)
    rotation = gimbal_to_body_rotation(sample, vehicle_quaternion)
    optical_axis_body = rotation @ camera_to_gimbal @ np.array([0.0, 0.0, 1.0])
    cosine = float(np.clip(optical_axis_body @ np.array([0.0, 0.0, 1.0]), -1, 1))
    downward_error_deg = math.degrees(math.acos(cosine))
    if downward_error_deg > max_downward_error_deg:
        raise ValueError(
            f"Gimbal is {downward_error_deg:.1f} deg from the downward landing envelope"
        )
    return rotation @ camera_to_gimbal @ camera_vector, downward_error_deg
