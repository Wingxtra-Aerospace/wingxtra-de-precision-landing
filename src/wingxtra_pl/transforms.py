from __future__ import annotations
import numpy as np


def rpy_deg_to_rotmat(roll_deg: float, pitch_deg: float, yaw_deg: float) -> np.ndarray:
    r = np.deg2rad(roll_deg)
    p = np.deg2rad(pitch_deg)
    y = np.deg2rad(yaw_deg)

    Rx = np.array([[1, 0, 0],
                   [0, np.cos(r), -np.sin(r)],
                   [0, np.sin(r),  np.cos(r)]], dtype=float)
    Ry = np.array([[ np.cos(p), 0, np.sin(p)],
                   [0,          1, 0],
                   [-np.sin(p), 0, np.cos(p)]], dtype=float)
    Rz = np.array([[np.cos(y), -np.sin(y), 0],
                   [np.sin(y),  np.cos(y), 0],
                   [0,          0,         1]], dtype=float)

    return Rz @ Ry @ Rx


def camera_to_body_ned_default(tvec_cam: np.ndarray) -> np.ndarray:
    """
    OpenCV camera coords: x right, y down, z forward.
    For a downward-facing camera, common mapping to BODY_NED:
      body x (forward) = camera z
      body y (right)   = camera x
      body z (down)    = camera y
    """
    x_cam, y_cam, z_cam = float(tvec_cam[0]), float(tvec_cam[1]), float(tvec_cam[2])
    return np.array([z_cam, x_cam, y_cam], dtype=float)
