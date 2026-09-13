from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List
import numpy as np


@dataclass(frozen=True)
class MarkerDef:
    marker_id: int
    family: str
    corners_xyz: np.ndarray  # shape (4, 3), meters, in TARGET frame


@dataclass(frozen=True)
class LandingTargetLayout:
    target_num: int
    markers: Dict[int, MarkerDef]  # keyed by marker_id

    @staticmethod
    def from_landmark_json(path: str) -> "LandingTargetLayout":
        """
        Landmark Landing Target export format (the one you provided):
          {
            "target_num": 0,
            "markers": [
              {
                "family": "tag36h11",
                "id": 90,
                "object_points": [[x,y,z], ...4 points...]
              },
              ...
            ]
          }

        """
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return LandingTargetLayout.from_dict(data)

    @staticmethod
    def from_dict(data: dict) -> "LandingTargetLayout":
        target_num = data.get("target_num", 0)
        if type(target_num) is not int or not 0 <= target_num <= 255:
            raise ValueError("target_num must be an integer between 0 and 255")
        markers_raw: List[dict] = data.get("markers", [])
        if not isinstance(markers_raw, list) or not 1 <= len(markers_raw) <= 100:
            raise ValueError("Board must contain between 1 and 100 markers")

        markers: Dict[int, MarkerDef] = {}
        for m in markers_raw:
            family = str(m.get("family", "")).strip()
            mid = m.get("id")
            if family != "tag36h11":
                raise ValueError("Only tag36h11 is supported")
            if type(mid) is not int or not 0 <= mid <= 586 or mid in markers:
                raise ValueError("Marker IDs must be unique integers between 0 and 586")
            obj = m.get("object_points")
            if obj is None or len(obj) != 4:
                raise ValueError(f"Marker {mid}: expected 4 object_points corners")

            corners_xyz = np.array(obj, dtype=float)
            if corners_xyz.shape != (4, 3) or not np.isfinite(corners_xyz).all():
                raise ValueError(f"Marker {mid}: corners must be a finite 4x3 matrix")
            if not np.allclose(corners_xyz[:, 2], 0, atol=1e-7):
                raise ValueError("Board corners must lie on the common z=0 plane")
            edges = np.roll(corners_xyz, -1, axis=0) - corners_xyz
            lengths = np.linalg.norm(edges, axis=1)
            if not 0.002 <= lengths.mean() <= 5 or not np.allclose(
                lengths, lengths.mean(), rtol=0.01
            ):
                raise ValueError(f"Marker {mid}: object_points must describe a square in metres")
            if not np.allclose(
                np.sum(edges * np.roll(edges, -1, axis=0), axis=1),
                0,
                atol=lengths.mean() ** 2 * 0.01,
            ):
                raise ValueError(f"Marker {mid}: corners must be ordered around the square")
            if np.max(np.abs(corners_xyz)) > 10:
                raise ValueError("Board coordinates exceed 10 metres; check units")
            markers[mid] = MarkerDef(marker_id=mid, family=family, corners_xyz=corners_xyz)

        return LandingTargetLayout(target_num=target_num, markers=markers)
