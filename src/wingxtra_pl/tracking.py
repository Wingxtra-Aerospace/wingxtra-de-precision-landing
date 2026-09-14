"""Measurement acceptance; rejected frames never refresh a track or get retransmitted."""

from __future__ import annotations

import numpy as np

from .config import QualityConfig


class TargetTracker:
    def __init__(self, quality: QualityConfig):
        self.q = quality
        self.reset()

    def reset(self):
        self.last_position = None
        self.last_time = None
        self.last_sequence = -1
        self.consecutive = 0
        self.reason = "Waiting for a target"

    def reject(self, reason: str):
        self.consecutive = 0
        self.reason = reason
        return False

    def accept(self, pose, body, captured: float, now: float, sequence: int) -> bool:
        if sequence <= self.last_sequence:
            return self.reject("Repeated frame")
        self.last_sequence = sequence
        if not 0 <= now - captured <= self.q.max_frame_age_s:
            return self.reject("Frame too old")
        if pose is None:
            return self.reject("Target not detected")
        p = np.asarray(body, dtype=float)
        if p.shape != (3,) or not np.isfinite(p).all() or p[2] <= 0:
            return self.reject("Target is not below the aircraft")
        distance = float(np.linalg.norm(p))
        if not self.q.min_distance_m <= distance <= self.q.max_distance_m:
            return self.reject("Target distance outside limits")
        if pose["num_markers_used"] < self.q.min_tags:
            return self.reject("Too few tags")
        error = pose["reproj_rmse_px"]
        if not np.isfinite(error) or error > self.q.max_reprojection_px:
            return self.reject("Reprojection error too high")
        if self.last_time is not None:
            dt = captured - self.last_time
            if dt <= 0:
                return self.reject("Non-monotonic frame timestamp")
            if dt > self.q.track_reset_s:
                self.last_position = None
                self.consecutive = 0
            elif np.linalg.norm(p - self.last_position) > (
                self.q.jump_allowance_m + self.q.max_relative_speed_m_s * dt
            ):
                return self.reject("Position jump rejected")
        self.last_position = p.copy()
        self.last_time = captured
        self.consecutive += 1
        if self.consecutive < self.q.reacquire_frames:
            self.reason = f"Acquiring target ({self.consecutive}/{self.q.reacquire_frames})"
            return False
        self.reason = "Target accepted"
        return True
