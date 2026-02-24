# Wingxtra DroneEngage Precision Landing (Single-Pi, Multi-Tag, No Rangefinder)

## Goal
Run precision landing on the **same Raspberry Pi** that runs DroneEngage (no extra Pi), using a downward IMX219 camera and a Landmark multi-tag target export (`landing-target.json`).

## Mandatory per-drone camera calibration (DO NOT SKIP)

This system **requires** a valid `camera.yaml` at runtime.
`camera.yaml` contains camera intrinsics and distortion coefficients used for pose estimation.
Without it, precision landing range/position will be wrong and landing may be unsafe.

### Policy (Wingxtra)
- **Every drone** + **every camera** must be calibrated.
- If the camera is replaced, moved, re-mounted, re-focused, or the capture resolution changes: **recalibrate and generate a new `camera.yaml`**.
- `camera.yaml` is aircraft configuration, not source code, so **do not commit it to Git**.
  (It is intentionally listed in `.gitignore`.)

### Generate `camera.yaml` on each drone
1. SSH into the drone’s Raspberry Pi (the one running DroneEngage).
2. Clone this repo onto that Pi.
3. Print a chessboard calibration sheet (10x7 squares, 9x6 inner corners recommended).
4. Measure square size accurately (meters) and set it in `tools/calibrate_camera.py` (`SQUARE_SIZE_M`).
5. Run calibration:

```bash
python3 tools/calibrate_camera.py
```

## Key requirement (non-negotiable)
**Do not open the FC serial MAVLink port from this project.**
DroneEngage owns the physical FC connection. This project outputs **INTERNAL MAVLink** to DroneEngage.

## Inputs
- `landing-target.json`: Landmark Landing Target export (AprilTag tag36h11, marker IDs, `object_points`).
- `camera.yaml`: camera intrinsics and distortion (generated with `tools/calibrate_camera.py`).
- IMX219 camera (Arducam IMX219 fixed focus) via Picamera2/libcamera.

## How pose is estimated
- Detect multiple AprilTags in a single frame (OpenCV ArUco AprilTag dictionary).
- Filter detections to IDs present in `landing-target.json`.
- Stack all detected tag corners (2D image points) with their 3D `object_points` (meters).
- Solve one pose with `solvePnP` over all points for stability and long-range acquisition.

## MAVLink output
- Construct MAVLink2 `LANDING_TARGET` with:
  - `frame = MAV_FRAME_BODY_NED`
  - `position_valid = 1`
  - `x, y, z` populated in meters (body frame)
- Send encoded MAVLink2 packet to DroneEngage via DataBus as INTERNAL MAVLink.
- DroneEngage forwards to FC on its existing MAVLink link.

## DataBus publisher
`src/wingxtra_pl/mavlink_out/databus_internal_mavlink.py` publishes MAVLink2
`LANDING_TARGET` packets to DroneEngage's internal bus endpoint and never opens a
physical FC serial port.

- Uses DataBus-like `sendBMSG` framing:
  - JSON metadata header including `andruav_message_id=6504`
  - a NULL separator byte (`\x00`)
  - raw MAVLink2 packet bytes
- `mavlink_out.internal_mavlink_cmd` configures the BMSG message-cmd string.

## Setup (on the DroneEngage Pi)
1. Install dependencies:
   - Raspberry Pi OS + libcamera
   - `sudo apt update`
   - `sudo apt install -y python3-pip`
   - `pip3 install -r requirements.txt`
2. Generate `camera.yaml`:
   - Print a chessboard (10x7 squares => 9x6 inner corners)
   - Measure square size, update `SQUARE_SIZE_M` in `tools/calibrate_camera.py`
   - Run `python3 tools/calibrate_camera.py`
3. Run:

```bash
python3 -m src.wingxtra_pl.main
```

### DataBus host/port overrides

Priority is `CLI > ENV > config.yaml`.

- CLI: `--databus-host` and `--databus-port`
- ENV: `DATABUS_HOST` and `DATABUS_PORT`
- Config fallback: `mavlink_out.databus_host` and `mavlink_out.databus_port`

If DataBus port is not provided from any source, the program fails fast with a clear error.

### Dry run / debug

```bash
python3 -m src.wingxtra_pl.main --dry-run --debug-overlay
```

## Quick code health check

Run this before deployment to ensure Python modules parse cleanly:

```bash
python -m py_compile $(rg --files src tools -g '*.py')
```

## Notes
- OpenCV dictionary must match target family: `tag36h11 => DICT_APRILTAG_36h11`.
- If axes are swapped (vehicle moves wrong), adjust `frames.cam_to_body_rpy_deg` in `config.yaml`.
