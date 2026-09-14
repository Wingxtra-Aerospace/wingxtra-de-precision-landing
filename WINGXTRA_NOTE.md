# Wingxtra runtime requirements

- Per-aircraft, per-camera calibration is mandatory before target output. The BlueOS service stores a validated `camera.json` in its persistent data directory. Never commit aircraft calibration data.
- Calibration must match the actual image resolution, source, camera identity and fixed lens profile. Changing focus, cropping, stabilization, zoom, camera or video geometry requires recalibration.
- The service never opens a physical MAVLink serial port. On BlueOS, use a local UDP endpoint provided by the BlueOS router. On a native DroneEngage installation, the advanced DataBus transport may be used with a separate raw telemetry feed for heartbeat supervision.
- Only one landing-target publisher may be active. The flight controller's link has one owner.
- AprilTag family is `tag36h11` / `DICT_APRILTAG_36h11`.
- Position messages use `MAV_FRAME_BODY_FRD`, `position_valid=1`, and a positive camera-to-board-origin distance.
- Camera translation belongs in ArduPilot `PLND_CAM_POS_*`; the companion applies only the configured camera-to-body rotation.
- Complete the commissioning record before operational use. Software test results alone do not establish flight qualification.

The former `camera.yaml` requirement and DataBus-only deployment instructions applied to the earlier native prototype. The current release supports the user-requested BlueOS integration and a browser calibration workflow. Use [README.md](README.md) and [docs/BLUEOS_INSTALL.md](docs/BLUEOS_INSTALL.md).
