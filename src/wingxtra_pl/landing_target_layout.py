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

        target_num = int(data.get("target_num", 0))
        markers_raw: List[dict] = data.get("markers", [])
        if not markers_raw:
            raise ValueError("landing-target.json has no 'markers'")

        markers: Dict[int, MarkerDef] = {}
        for m in markers_raw:
            family = str(m.get("family", "")).strip()
            mid = int(m.get("id"))
            obj = m.get("object_points")
            if obj is None or len(obj) != 4:
                raise ValueError(f"Marker {mid}: expected 4 object_points corners")

            corners_xyz = np.array(obj, dtype=float).reshape(4, 3)
            markers[mid] = MarkerDef(
                marker_id=mid, family=family, corners_xyz=corners_xyz
            )

        return LandingTargetLayout(target_num=target_num, markers=markers)
