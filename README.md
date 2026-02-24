# Wingxtra DroneEngage Precision Landing (Single-Pi, Multi-Tag, No Rangefinder)

## Goal
Run precision landing on the SAME Raspberry Pi that runs DroneEngage (no extra Pi),
using a downward IMX219 camera and a Landmark multi-tag target export (`landing-target.json`).

Key requirement: DO NOT open the FC serial MAVLink port from this project.
DroneEngage owns the physical FC connection. This project outputs INTERNAL MAVLink to DroneEngage.

## Inputs
- `landing-target.json`: Landmark Landing Target export (AprilTag tag36h11, marker IDs, object_points).
- `camera.yaml`: camera intrinsics & distortion (generated with `tools/calibrate_camera.py`).
- IMX219 camera (Arducam IMX219 fixed focus) via Picamera2/libcamera.

## How pose is estimated
- Detect multiple AprilTags in a single frame (OpenCV aruco AprilTag dictionary).
- Filter detections to the IDs present in `landing-target.json`.
- Stack all detected tag corners (2D image points) with their 3D `object_points` (meters).
- Solve ONE pose with solvePnP over all points for stability and long-range acquisition.

## MAVLink output
- Construct MAVLink2 `LANDING_TARGET` with:
  - frame = MAV_FRAME_BODY_NED
  - position_valid = 1
  - x,y,z populated in meters (body frame)
- Send the encoded MAVLink2 packet to DroneEngage via DataBus as INTERNAL MAVLink.
- DroneEngage forwards to FC on its existing MAVLink link.

### TODO for Codex (important)
Implement `DroneEngageDatabusInternalMavlinkOut.send_landing_target()` in:
`src/wingxtra_pl/mavlink_out/databus_internal_mavlink.py`

It must publish the raw MAVLink2 bytes as an INTERNAL MAVLink message through DroneEngage DataBus.

## Setup (on the DroneEngage Pi)
1) Install deps:
   - Raspberry Pi OS + libcamera
   - `sudo apt update`
   - `sudo apt install -y python3-pip`
   - `pip3 install -r requirements.txt`

2) Generate camera.yaml:
   - Print a chessboard (10x7 squares => 9x6 inner corners)
   - Measure square size, update SQUARE_SIZE_M in tools/calibrate_camera.py
   - Run: `python3 tools/calibrate_camera.py`

3) Run:
   - `python3 -m src.wingxtra_pl.main`

## Notes
- OpenCV dictionary must match the target family: tag36h11 => DICT_APRILTAG_36h11.
- If axes are swapped (vehicle moves wrong), adjust `frames.cam_to_body_rpy_deg` in config.yaml.
