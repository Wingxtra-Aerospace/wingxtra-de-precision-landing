from __future__ import annotations

import cv2
import numpy as np
from dataclasses import dataclass
from .landing_target_layout import LandingTargetLayout


def _dict_by_name(name: str):
    if not hasattr(cv2.aruco, name):
        raise ValueError(f"OpenCV aruco does not have dictionary '{name}'")
    return cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, name))


@dataclass
class DetectorConfig:
    opencv_dictionary: str


class MultiTagPoseEstimator:
    """
    Uses OpenCV ArUco module with AprilTag dictionaries (opencv-contrib-python required).
    For AprilTag 36h11: opencv_dictionary = "DICT_APRILTAG_36h11"
    """

    def __init__(self, cfg: DetectorConfig, layout: LandingTargetLayout, camera_matrix: np.ndarray, dist_coeffs: np.ndarray):
        self.cfg = cfg
        self.layout = layout
        self.K = camera_matrix
        self.dist = dist_coeffs

        dictionary = _dict_by_name(cfg.opencv_dictionary)
        params = cv2.aruco.DetectorParameters()
        self.detector = cv2.aruco.ArucoDetector(dictionary, params)

    def estimate(self, frame_bgr: np.ndarray):
        corners, ids, _ = self.detector.detectMarkers(frame_bgr)
        if ids is None or len(ids) == 0:
            return None

        ids_list = ids.flatten().tolist()

        obj_pts_all = []
        img_pts_all = []
        used_ids = []

        for i, mid in enumerate(ids_list):
            if mid not in self.layout.markers:
                continue

            img_pts = corners[i].reshape((4, 2)).astype(np.float32)
            obj_pts = self.layout.markers[mid].corners_xyz.astype(np.float32)

            img_pts_all.append(img_pts)
            obj_pts_all.append(obj_pts)
            used_ids.append(mid)

        if not obj_pts_all:
            return None

        obj_pts_all = np.concatenate(obj_pts_all, axis=0)  # (4N, 3)
        img_pts_all = np.concatenate(img_pts_all, axis=0)  # (4N, 2)

        ok, rvec, tvec = cv2.solvePnP(
            obj_pts_all,
            img_pts_all,
            self.K,
            self.dist,
            flags=cv2.SOLVEPNP_ITERATIVE,
        )
        if not ok:
            return None

        tvec = tvec.reshape(3).astype(float)

        # Optional angles (useful for debugging)
        x, y, z = float(tvec[0]), float(tvec[1]), float(tvec[2])
        angle_x = float(np.arctan2(x, z))
        angle_y = float(np.arctan2(y, z))

        return {
            "rvec": rvec,
            "tvec": tvec,                 # TARGET origin in camera frame
            "angle_x": angle_x,
            "angle_y": angle_y,
            "used_ids": used_ids,
            "num_markers_used": len(used_ids),
        }
