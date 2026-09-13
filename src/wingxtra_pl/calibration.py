"""Camera calibration tied to the actual source, lens profile and image dimensions."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

import cv2
import numpy as np
from pydantic import Field, model_validator

from .config import CameraConfig, Model


class Calibration(Model):
    schema_version: Literal[1] = 1
    camera_fingerprint: str = Field(min_length=64, max_length=64)
    image_width: int = Field(ge=320, le=3840)
    image_height: int = Field(ge=240, le=2160)
    camera_matrix: list[list[float]]
    distortion_coefficients: list[float]
    rms_px: float = Field(ge=0, le=1)
    per_view_rms_px: list[float] = Field(min_length=15, max_length=60)
    views: int = Field(ge=15, le=60)
    created_utc: str

    @model_validator(mode="after")
    def valid_intrinsics(self):
        k = np.asarray(self.camera_matrix, dtype=float)
        d = np.asarray(self.distortion_coefficients, dtype=float)
        if k.shape != (3, 3) or not np.isfinite(k).all():
            raise ValueError("Camera matrix must be finite and 3x3")
        w, h = self.image_width, self.image_height
        if not (
            0.1 * w < k[0, 0] < 10 * w
            and 0.1 * h < k[1, 1] < 10 * h
            and 0 < k[0, 2] < w
            and 0 < k[1, 2] < h
            and np.allclose(k[2], [0, 0, 1])
            and abs(k[0, 1]) < 1e-8
            and abs(k[1, 0]) < 1e-8
        ):
            raise ValueError("Implausible camera intrinsics")
        if d.ndim != 1 or len(d) not in {4, 5, 8, 12, 14} or not np.isfinite(d).all():
            raise ValueError("Invalid distortion coefficients")
        errors = np.asarray(self.per_view_rms_px)
        if (
            len(errors) != self.views
            or not np.isfinite(errors).all()
            or (np.min(errors) < 0 or np.max(errors) > 2)
        ):
            raise ValueError("Each calibration view must have RMS at most 2 pixels")
        return self

    def matches(self, camera: CameraConfig) -> bool:
        return (
            self.camera_fingerprint == camera.fingerprint()
            and self.image_width == camera.width
            and self.image_height == camera.height
        )


class CalibrationSession:
    def __init__(self, camera: CameraConfig, columns=9, rows=6, square_m=0.0245):
        if not (3 <= columns <= 15 and 3 <= rows <= 15 and 0.005 <= square_m <= 0.15):
            raise ValueError("Use 3–15 inner corners per axis and 5–150 mm squares")
        self.camera = camera.model_copy(deep=True)
        self.pattern = (columns, rows)
        self.square_m = square_m
        self.objects = np.zeros((columns * rows, 3), np.float32)
        self.objects[:, :2] = np.mgrid[0:columns, 0:rows].T.reshape(-1, 2) * square_m
        self.points = []
        self.sequences = set()

    def capture(self, frame, sequence: int):
        if frame.shape[:2] != (self.camera.height, self.camera.width):
            raise ValueError("Actual camera resolution differs from configuration")
        if sequence in self.sequences:
            raise ValueError("Wait for a new camera frame")
        if len(self.points) >= 60:
            raise ValueError("Session is full; solve calibration or start again")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ok, corners = cv2.findChessboardCornersSB(gray, self.pattern)
        if not ok:
            raise ValueError("Chessboard not found; show every inner corner and improve lighting")
        p = corners.reshape(-1, 2)
        if min(np.ptp(p[:, 0]), np.ptp(p[:, 1])) < 80:
            raise ValueError("Move the chessboard closer; it is too small in the image")
        if any(
            np.sqrt(np.mean((p - old.reshape(-1, 2)) ** 2))
            < (0.025 * min(self.camera.width, self.camera.height))
            for old in self.points
        ):
            raise ValueError("View too similar; move or tilt the chessboard")
        self.points.append(corners.astype(np.float32))
        self.sequences.add(sequence)
        return self.status()

    def status(self):
        cells, scales, skews = set(), [], []
        c, r = self.pattern
        for corners in self.points:
            p = corners.reshape(r, c, 2)
            centre = p.mean(axis=(0, 1))
            cells.add(
                (
                    min(2, int(centre[0] / self.camera.width * 3)),
                    min(2, int(centre[1] / self.camera.height * 3)),
                )
            )
            a = np.linalg.norm(p[0, -1] - p[0, 0])
            b = np.linalg.norm(p[-1, -1] - p[-1, 0])
            left = np.linalg.norm(p[-1, 0] - p[0, 0])
            right = np.linalg.norm(p[-1, -1] - p[0, -1])
            scales.append(float(np.sqrt(max(a * left, 1))))
            skews.append(max(abs(a - b) / max(a, b, 1), abs(left - right) / max(left, right, 1)))
        spread = max(scales) / min(scales) if scales else 0
        tilted = sum(s > 0.08 for s in skews)
        ready = len(self.points) >= 15 and len(cells) >= 4 and spread >= 1.5 and tilted >= 3
        return {
            "views": len(self.points),
            "coverage_cells": len(cells),
            "scale_ratio": round(spread, 2),
            "tilted_views": tilted,
            "ready": ready,
            "columns": c,
            "rows": r,
            "square_m": self.square_m,
            "guidance": "Capture 15+ views across 4 of 9 image regions, at varied distances, "
            "including at least 3 tilted views. Keep focus and zoom fixed.",
        }

    def solve(self) -> Calibration:
        if not self.status()["ready"]:
            raise ValueError(
                "More varied calibration views are needed: " + self.status()["guidance"]
            )
        rms, k, d, rvecs, tvecs = cv2.calibrateCamera(
            [self.objects] * len(self.points),
            self.points,
            (self.camera.width, self.camera.height),
            None,
            None,
        )
        errors = []
        for points, r, t in zip(self.points, rvecs, tvecs):
            projected = cv2.projectPoints(self.objects, r, t, k, d)[0]
            errors.append(float(np.sqrt(np.mean(np.sum((points - projected) ** 2, axis=2)))))
        return Calibration(
            camera_fingerprint=self.camera.fingerprint(),
            image_width=self.camera.width,
            image_height=self.camera.height,
            camera_matrix=k.tolist(),
            distortion_coefficients=d.flatten().tolist(),
            rms_px=float(rms),
            per_view_rms_px=errors,
            views=len(self.points),
            created_utc=datetime.now(timezone.utc).isoformat(),
        )


def chessboard_svg(columns: int = 9, rows: int = 6, square_mm: float = 24.5) -> str:
    if not (3 <= columns <= 15 and 3 <= rows <= 15 and 5 <= square_mm <= 150):
        raise ValueError("Invalid chessboard dimensions")
    w, h = (columns + 3) * square_mm, (rows + 3) * square_mm
    squares = "".join(
        f'<rect x="{(x + 1) * square_mm}" y="{(y + 1) * square_mm}" '
        f'width="{square_mm}" height="{square_mm}"/>'
        for y in range(rows + 1)
        for x in range(columns + 1)
        if (x + y) % 2 == 0
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" '
        f'viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="white"/>'
        f'<g fill="black">{squares}</g></svg>'
    )
