import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from wingxtra_pl.calibration import Calibration
from wingxtra_pl.config import CameraConfig
from wingxtra_pl.landing_target_layout import LandingTargetLayout


@pytest.fixture
def camera():
    return CameraConfig(width=1280, height=720)


@pytest.fixture
def intrinsics():
    return np.array([[850.0, 0, 640], [0, 850, 360], [0, 0, 1]])


@pytest.fixture
def board_data():
    markers = []
    for mid, x, y in [(3, -0.23, -0.18), (12, 0.06, -0.18), (41, -0.23, 0.08), (77, 0.06, 0.08)]:
        s = 0.15
        markers.append(
            {
                "id": mid,
                "family": "tag36h11",
                "object_points": [[x, y, 0], [x + s, y, 0], [x + s, y + s, 0], [x, y + s, 0]],
            }
        )
    return {"target_num": 0, "markers": markers}


@pytest.fixture
def layout(board_data):
    return LandingTargetLayout.from_dict(board_data)


@pytest.fixture
def original_layout():
    path = Path(__file__).parents[1] / "landing-target.json"
    return LandingTargetLayout.from_dict(json.loads(path.read_text()))


@pytest.fixture
def calibration(camera, intrinsics):
    return Calibration(
        camera_fingerprint=camera.fingerprint(),
        image_width=1280,
        image_height=720,
        camera_matrix=intrinsics.tolist(),
        distortion_coefficients=[0] * 5,
        rms_px=0.3,
        per_view_rms_px=[0.3] * 15,
        views=15,
        created_utc="2026-09-13T00:00:00Z",
    )


def projected_corners(layout, k, r=None, t=None):
    r = np.array([0.2, -0.1, 0.02]) if r is None else np.asarray(r, dtype=float)
    t = np.array([0.05, -0.04, 1.4]) if t is None else np.asarray(t, dtype=float)
    corners = [
        cv2.projectPoints(m.corners_xyz, r, t, k, np.zeros(5))[0].reshape(1, 4, 2)
        for m in layout.markers.values()
    ]
    return corners, np.array(list(layout.markers)).reshape(-1, 1)


def render_board(layout, k, r=None, t=None, size=(1280, 720)):
    corners, ids = projected_corners(layout, k, r, t)
    image = np.full((size[1], size[0]), 255, np.uint8)
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
    for p, mid in zip(corners, ids.flatten()):
        tag = (
            cv2.aruco.generateImageMarker(dictionary, int(mid), 256)
            if hasattr(cv2.aruco, "generateImageMarker")
            else cv2.aruco.drawMarker(dictionary, int(mid), 256)
        )
        transform = cv2.getPerspectiveTransform(
            np.array([[0, 0], [255, 0], [255, 255], [0, 255]], np.float32),
            p.reshape(4, 2).astype(np.float32),
        )
        warped = cv2.warpPerspective(tag, transform, size, borderValue=255)
        image = np.minimum(image, warped)
    return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
