# Camera profiles and installation modes

The extension supports two explicit geometry modes and several connection
presets. These are separate choices:

- A **camera profile** fills known stream defaults. It does not supply camera
  calibration, prove driver compatibility or qualify the hardware.
- **Fixed mode** applies the configured constant OpenCV-camera-to-BODY_FRD
  rotation and has no gimbal telemetry dependency.
- **Gimbal mode** combines each vision vector with
  `GIMBAL_DEVICE_ATTITUDE_STATUS`. It fails closed when the selected device is
  missing, unhealthy, stale, ambiguously framed, too far from the frame receipt
  time, or outside the configured downward envelope.

## Included connection presets

The initial presets mirror the camera choices and RTSP defaults reviewed in
BlueOS-community/blueos-precision-landing: SIYI A8 Mini, ZR10, ZT6 visible and
thermal streams, and XFRobot Z1 Mini. Their values remain editable. A custom
profile retains RTSP, HTTP MJPEG, V4L2 and native Picamera2 sources.

The reference implementation's selector is useful UI, but its presets are not
evidence of camera calibration. Wingxtra therefore does not bundle its single
XFRobot calibration or use a horizontal-FOV approximation. The existing
calibration workflow still solves and verifies the exact Wingxtra camera
identity, source, lens profile and image geometry.

## Gimbal coordinate and timing contract

The vision estimator returns the board origin in OpenCV camera axes
(`x` right, `y` down, `z` optical-forward). `camera_to_gimbal` maps that
vector into gimbal-device FRD. The MAVLink quaternion then maps gimbal-device
FRD into vehicle BODY_FRD. Explicit vehicle-yaw-frame status is accepted
directly. Earth-yaw-frame status requires finite `delta_yaw`; conflicting flags
or missing conversion data are rejected.

The initial time alignment uses Linux kernel receive timestamps for MAVLink and
the local decoded-frame receipt timestamp. The closest matching sample must be
within `max_sample_skew_s`, and it must remain inside `status_timeout_s`.
This bounds obvious stale/misaligned data but does not recover the physical
exposure time of a buffered network stream. Measure camera transport delay and
gimbal telemetry latency on the intended CM4/camera combination before flight.

## Gimbal pointing ownership

The companion extension transforms and validates measured gimbal attitude; it
does not command the gimbal. The Wingxtra QuadPlane applet offers two choices:

- external/operator pointing, with measured attitude required; or
- an explicit opt-in command to the selected AP_Mount instance during active
  precision landing.

Only one controller may own the gimbal. Confirm operator override, transition,
target-loss and total-companion-failure behaviour in the selected firmware
before enabling applet control. Fixed mode never calls the mount API.

## Calibration procedure

Select the profile and mode, confirm the actual stream resolution, lock the
focus/zoom/crop, then run the built-in multi-view calibration. Changing the
mount mode or profile label alone does not invalidate the intrinsic
calibration; changing camera identity, stream URL, lens profile or resolution
does. A zoom camera needs a separate named lens profile and calibration for
every supported zoom position.

No listed camera/gimbal is flight-qualified merely because it appears in the
selector.
