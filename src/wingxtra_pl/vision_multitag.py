"""Joint board pose from all visible known tags, with whole-tag outlier rejection."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from .landing_target_layout import LandingTargetLayout


@dataclass
class DetectorConfig:
    opencv_dictionary: str = "DICT_APRILTAG_36h11"
    min_tag_edge_px: float = 12
    max_reprojection_px: float = 3


class MultiTagPoseEstimator:
    def __init__(
        self,
        cfg: DetectorConfig,
        layout: LandingTargetLayout,
        camera_matrix: np.ndarray,
        dist_coeffs: np.ndarray,
    ):
        if cfg.opencv_dictionary != "DICT_APRILTAG_36h11":
            raise ValueError("This board format requires DICT_APRILTAG_36h11")
        self.cfg, self.layout = cfg, layout
        self.K = np.asarray(camera_matrix, dtype=np.float64)
        self.dist = np.asarray(dist_coeffs, dtype=np.float64)
        self.dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_36h11)
        # Debian Bookworm OpenCV 4.6 and pip OpenCV >=4.7 both supported.
        self.params = (
            cv2.aruco.DetectorParameters()
            if hasattr(cv2.aruco, "ArucoDetector")
            else cv2.aruco.DetectorParameters_create()
        )
        self.params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
        self.detector = (
            cv2.aruco.ArucoDetector(self.dictionary, self.params)
            if hasattr(cv2.aruco, "ArucoDetector")
            else None
        )

    def detect(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) if frame.ndim == 3 else frame
        if self.detector is not None:
            corners, ids, _ = self.detector.detectMarkers(gray)
        else:
            corners, ids, _ = cv2.aruco.detectMarkers(gray, self.dictionary, parameters=self.params)
        return corners, ids

    def estimate(self, frame):
        return self.estimate_corners(*self.detect(frame))

    def estimate_corners(self, corners, ids):
        if ids is None:
            return None
        selected = []
        all_ids = [int(i) for i in np.asarray(ids).flatten()]
        # A duplicated ID cannot identify a unique physical board corner.
        for corner, mid in zip(corners, all_ids):
            if mid not in self.layout.markers or all_ids.count(mid) != 1:
                continue
            p = np.asarray(corner, dtype=np.float64).reshape(4, 2)
            if not np.isfinite(p).all():
                continue
            if np.min(np.linalg.norm(p - np.roll(p, -1, axis=0), axis=1)) < (
                self.cfg.min_tag_edge_px
            ):
                continue
            selected.append((mid, self.layout.markers[mid].corners_xyz, p))
        if not selected:
            return None
        obj = np.concatenate([s[1] for s in selected]).astype(np.float64)
        img = np.concatenate([s[2] for s in selected]).astype(np.float64)
        try:
            if len(selected) >= 2:
                ok, r, t, inliers = cv2.solvePnPRansac(
                    obj,
                    img,
                    self.K,
                    self.dist,
                    iterationsCount=100,
                    reprojectionError=self.cfg.max_reprojection_px,
                    confidence=0.999,
                    flags=cv2.SOLVEPNP_EPNP,
                )
                if not ok or inliers is None:
                    return None
                inlier_set = set(inliers.flatten().tolist())
                retained = [
                    i
                    for i in range(len(selected))
                    if all(4 * i + k in inlier_set for k in range(4))
                ]
                # Do not silently reduce contradictory multi-tag evidence to one tag.
                if len(retained) < 2:
                    return None
                selected = [selected[i] for i in retained]
                obj = np.concatenate([s[1] for s in selected]).astype(np.float64)
                img = np.concatenate([s[2] for s in selected]).astype(np.float64)
            # IPPE returns both planar solutions; choose physically visible minimum error.
            result = cv2.solvePnPGeneric(obj, img, self.K, self.dist, flags=cv2.SOLVEPNP_IPPE)
            candidates = []
            for r, t in zip(result[1], result[2]):
                if not np.isfinite(r).all() or not np.isfinite(t).all():
                    continue
                rotation = cv2.Rodrigues(r)[0]
                if np.any((obj @ rotation.T + t.reshape(3))[:, 2] <= 0) or t[2, 0] <= 0:
                    continue
                projected = cv2.projectPoints(obj, r, t, self.K, self.dist)[0].reshape(-1, 2)
                errors = np.linalg.norm(img - projected, axis=1)
                rms = float(np.sqrt(np.mean(errors**2)))
                if np.isfinite(rms):
                    candidates.append((rms, r, t, errors))
            if not candidates:
                return None
            rms, r, t, errors = min(candidates, key=lambda c: c[0])
            if rms > self.cfg.max_reprojection_px or np.max(errors) > (
                2 * self.cfg.max_reprojection_px
            ):
                return None
        except cv2.error:
            return None
        t = t.reshape(3)
        return {
            "rvec": r,
            "tvec": t,
            "angle_x": float(np.arctan2(t[0], t[2])),
            "angle_y": float(np.arctan2(t[1], t[2])),
            "used_ids": [s[0] for s in selected],
            "num_markers_used": len(selected),
            "reproj_rmse_px": rms,
            "image_corners": [s[2] for s in selected],
        }
