"""Known camera connection presets.

Presets populate connection fields only. They are not factory calibration files and do
not constitute hardware qualification; every installed lens, focus, resolution and
video mode still requires calibration and bench validation.
"""

from __future__ import annotations

from copy import deepcopy

CAMERA_PROFILES = {
    "custom": {
        "label": "Custom camera",
        "recommended_mode": "fixed",
    },
    "siyi-a8": {
        "label": "SIYI A8 Mini",
        "recommended_mode": "gimbal",
        "kind": "rtsp",
        "source": "rtsp://192.168.144.25:8554/main.264",
        "camera_id": "siyi-a8",
        "lens_profile": "visible-fixed-focus",
        "width": 1280,
        "height": 720,
        "fps": 30,
    },
    "siyi-zr10": {
        "label": "SIYI ZR10",
        "recommended_mode": "gimbal",
        "kind": "rtsp",
        "source": "rtsp://192.168.144.25:8554/main.264",
        "camera_id": "siyi-zr10",
        "lens_profile": "visible-zoom-position",
        "width": 1280,
        "height": 720,
        "fps": 30,
    },
    "siyi-zt6-ir": {
        "label": "SIYI ZT6 thermal stream",
        "recommended_mode": "gimbal",
        "kind": "rtsp",
        "source": "rtsp://192.168.144.25:8554/video1",
        "camera_id": "siyi-zt6-ir",
        "lens_profile": "thermal-fixed-focus",
        "width": 640,
        "height": 512,
        "fps": 30,
    },
    "siyi-zt6-rgb": {
        "label": "SIYI ZT6 visible stream",
        "recommended_mode": "gimbal",
        "kind": "rtsp",
        "source": "rtsp://192.168.144.25:8554/video2",
        "camera_id": "siyi-zt6-rgb",
        "lens_profile": "visible-fixed-focus",
        "width": 1280,
        "height": 720,
        "fps": 30,
    },
    "xfrobot-z1-mini": {
        "label": "XFRobot Z1 Mini",
        "recommended_mode": "gimbal",
        "kind": "rtsp",
        "source": "rtsp://192.168.144.108",
        "camera_id": "xfrobot-z1-mini",
        "lens_profile": "visible-fixed-focus",
        "width": 1920,
        "height": 1080,
        "fps": 30,
    },
}


def camera_profiles():
    return deepcopy(CAMERA_PROFILES)
