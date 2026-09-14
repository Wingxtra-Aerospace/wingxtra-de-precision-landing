from __future__ import annotations

import hashlib
import json
import re
from typing import Literal
from urllib.parse import urlsplit

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True, allow_inf_nan=False)


class CameraConfig(Model):
    profile: str = Field(default="custom", pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")
    mode: Literal["fixed", "gimbal"] = "fixed"
    kind: Literal["rtsp", "mjpeg", "v4l2", "picamera2"] = "rtsp"
    source: str = Field(default="rtsp://127.0.0.1:8554/landing", max_length=512)
    camera_id: str = Field(default="landing-camera", min_length=1, max_length=80)
    lens_profile: str = Field(default="fixed-focus", min_length=1, max_length=80)
    width: int = Field(default=1280, ge=320, le=3840)
    height: int = Field(default=720, ge=240, le=2160)
    fps: int = Field(default=30, ge=5, le=60)

    @model_validator(mode="after")
    def source_valid(self):
        if self.kind in {"rtsp", "mjpeg"}:
            url = urlsplit(self.source)
            schemes = {"rtsp", "rtsps"} if self.kind == "rtsp" else {"http", "https"}
            if url.scheme not in schemes or not url.hostname:
                raise ValueError(f"{self.kind} camera requires a valid network URL")
        elif self.kind == "v4l2" and not re.fullmatch(r"/dev/video[0-9]+", self.source):
            raise ValueError("USB camera source must be a /dev/videoN device")
        elif self.kind == "picamera2" and not self.source.isdigit():
            raise ValueError("Picamera2 source must be a camera index, e.g. 0")
        return self

    def fingerprint(self) -> str:
        data = self.model_dump(exclude={"fps", "profile", "mode"})
        return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


class MountConfig(Model):
    # Image top toward nose. OpenCV x=right,y=down,z=optical forward.
    camera_to_body: list[list[float]] = Field(
        default_factory=lambda: [[0, -1, 0], [1, 0, 0], [0, 0, 1]]
    )

    @model_validator(mode="after")
    def rotation_valid(self):
        r = np.asarray(self.camera_to_body, dtype=float)
        if r.shape != (3, 3) or not np.all(np.isfinite(r)):
            raise ValueError("Mount rotation must be a finite 3x3 matrix")
        if not np.allclose(r.T @ r, np.eye(3), atol=1e-5) or not np.isclose(
            np.linalg.det(r), 1, atol=1e-5
        ):
            raise ValueError("Mount rotation must be orthonormal with determinant +1")
        return self


class GimbalConfig(Model):
    # OpenCV camera axes -> gimbal-device FRD. Default: optical axis is gimbal forward.
    camera_to_gimbal: list[list[float]] = Field(
        default_factory=lambda: [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    )
    component_id: int = Field(default=0, ge=0, le=255)
    device_id: int = Field(default=0, ge=0, le=6)
    status_timeout_s: float = Field(default=0.5, ge=0.1, le=2)
    max_sample_skew_s: float = Field(default=0.15, ge=0.02, le=0.5)
    max_downward_error_deg: float = Field(default=10, ge=1, le=45)

    @model_validator(mode="after")
    def rotation_valid(self):
        r = np.asarray(self.camera_to_gimbal, dtype=float)
        if r.shape != (3, 3) or not np.all(np.isfinite(r)):
            raise ValueError("Camera-to-gimbal rotation must be a finite 3x3 matrix")
        if not np.allclose(r.T @ r, np.eye(3), atol=1e-5) or not np.isclose(
            np.linalg.det(r), 1, atol=1e-5
        ):
            raise ValueError(
                "Camera-to-gimbal rotation must be orthonormal with determinant +1"
            )
        return self


class OutputConfig(Model):
    mode: Literal["udp", "droneengage_databus"] = "udp"
    listen_host: str = Field(default="127.0.0.1", min_length=1, max_length=80)
    listen_port: int = Field(default=14771, ge=1024, le=65535)
    peer_host: str = Field(default="127.0.0.1", min_length=1, max_length=80)
    target_system: int = Field(default=1, ge=1, le=255)
    source_component: int = Field(default=193, ge=2, le=255)
    heartbeat_timeout_s: float = Field(default=3.0, ge=0.5, le=10)
    send_hz: float = Field(default=20, ge=5, le=50)
    databus_host: str = Field(default="127.0.0.1", min_length=1, max_length=80)
    databus_port: int = Field(default=60000, ge=1024, le=65535)
    databus_module_key: str = Field(
        default="wingxtra-precision-landing", min_length=1, max_length=80
    )


class QualityConfig(Model):
    max_frame_age_s: float = Field(default=0.25, ge=0.05, le=0.5)
    max_reprojection_px: float = Field(default=3, ge=0.2, le=8)
    min_tag_edge_px: float = Field(default=12, ge=6, le=100)
    min_tags: int = Field(default=1, ge=1, le=10)
    min_distance_m: float = Field(default=0.1, ge=0.02, le=2)
    max_distance_m: float = Field(default=30, ge=1, le=100)
    reacquire_frames: int = Field(default=3, ge=2, le=20)
    max_relative_speed_m_s: float = Field(default=6, gt=0, le=30)
    jump_allowance_m: float = Field(default=0.15, ge=0.02, le=2)
    track_reset_s: float = Field(default=0.5, ge=0.1, le=2)

    @model_validator(mode="after")
    def distance_order(self):
        if self.min_distance_m >= self.max_distance_m:
            raise ValueError("Minimum distance must be less than maximum distance")
        return self


class Config(Model):
    schema_version: Literal[1] = 1
    camera: CameraConfig = Field(default_factory=CameraConfig)
    mount: MountConfig = Field(default_factory=MountConfig)
    gimbal: GimbalConfig = Field(default_factory=GimbalConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    startup_mode: Literal["stopped", "monitor", "publish"] = "stopped"
