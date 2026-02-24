# WINGXTRA NOTE (MANDATORY)

**Per-drone camera calibration is mandatory.**

**This project requires `camera.yaml` at runtime and will fail fast if it is missing or if its
resolution does not match `config.yaml` camera width/height.**

**`camera.yaml` is aircraft-specific calibration data and MUST NOT be committed to git.**

## Runtime / integration non-negotiables

- **Single Pi / single FC link:** this module must **NOT** open `/dev/serial0` or any physical
  MAVLink serial port.
- **INTERNAL MAVLink only:** this module sends `LANDING_TARGET` to DroneEngage via DataBus;
  DroneEngage forwards to FC.
- **AprilTag family:** use OpenCV ArUco `DICT_APRILTAG_36h11` (matching Landmark `tag36h11`).
- **No rangefinder mode:** use PnP-derived `x,y,z` in meters with
  `LANDING_TARGET.position_valid = 1`.

## If calibration is missing

Run:

```bash
python3 tools/calibrate_camera.py
```
