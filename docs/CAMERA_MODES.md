# Camera profiles and installation modes

The extension supports two explicit geometry modes and several connection
presets. These are separate choices:

- A **camera profile** fills known stream defaults. It does not supply camera
  calibration, prove driver compatibility or qualify the hardware.
- **Fixed mode** applies the configured constant OpenCV-camera-to-BODY_FRD
  rotation and has no gimbal telemetry dependency.
- **Gimbal mode** combines each vision vector with
  `GIMBAL_DEVICE_ATTITUDE_STATUS` and autopilot `ATTITUDE` or
  `ATTITUDE_QUATERNION`. It fails closed when either attitude stream is
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
vector into gimbal-device FRD. The gimbal quaternion maps that vector into
either NED or a level frame aligned with vehicle heading, according to the
MAVLink yaw flags. A heading frame does not include aircraft roll/pitch.
The extension composes the full measured aircraft rotation to obtain BODY_FRD:

- Earth frame: `R_body_to_ned.T @ R_gimbal_to_ned`.
- Vehicle-heading frame:
  `R_body_to_ned.T @ R_heading_to_ned @ R_gimbal_to_heading`.

Aircraft attitude comes only from the configured target system's autopilot
component (1), through the same validated router peer and fresh heartbeat.
`ATTITUDE` uses intrinsic ZYX Euler angles; `ATTITUDE_QUATERNION` uses the
body-to-NED quaternion, without its display-only `repr_offset_q`. Explicit
frame flags take precedence; legacy flags use `YAW_LOCK`. `delta_yaw` is not
needed with full aircraft attitude, including on legacy reports where the
protocol requires ignoring that field. Conflicting flags, invalid attitudes
and an undefined vehicle heading are rejected.

The configured downward-angle envelope retains its original meaning: optical
axis relative to **BODY_FRD down**, not earth down. A stabilised nadir camera
can therefore leave that envelope when the aircraft tilts. No configured
angle limit is increased by this correction.

The initial time alignment uses Linux kernel receive timestamps for MAVLink and
the local decoded-frame receipt timestamp. Each closest matching attitude must
be within `max_sample_skew_s` of the frame and inside `status_timeout_s` at
use. Aircraft and gimbal samples must also be within `max_sample_skew_s` of
each other. Configure the router to deliver both required attitude streams at
rates that satisfy those existing limits; this change sends no stream-rate or
aircraft-setting commands.
This bounds obvious stale/misaligned data but does not recover the physical
exposure time of a buffered network stream. Measure camera transport delay and
gimbal telemetry latency on the intended CM4/camera combination before flight.

Device-clock handling is separate from receive-time matching:

- The first timestamp primes the clock; at least one strictly advancing sample
  is required before output. Clocks are separate for each gimbal component/device
  and for the autopilot. Multiple matching gimbals require explicit selection.
- Repeated or reordered device timestamps do not update an accepted sample or
  its receive age. Existing samples expire normally under the same age/skew
  limits, even if cached status packets and heartbeats keep arriving.
- Unsigned 32-bit wrap is accepted only for a forward modular difference below
  half the counter range and consistent with elapsed receive time plus the
  configured heartbeat timeout (the router's existing maximum packet age).
  Large jumps and backwards counters do not lower or rebase the high-water mark.
- After a device reboot, re-establish the telemetry session on the ground by
  restarting the extension or saving setup while freshly disarmed. Merely
  stopping/starting the camera does not reset telemetry clocks. A validated
  router-peer change also discards history and requires new clock progress.
  Aircraft response to lost precision-landing data remains the separate R04/F03
  recovery-policy gate.
- A new invalid quaternion or gimbal fault clears that source's healthy history;
  an older nearby sample cannot hide the fault. A device that advances timestamps
  while emitting a frozen estimate is not detectable from timestamp progression
  alone. Exposure-time synchronisation and that residual failure remain unqualified.

Protocol references: [attitude messages and gimbal status](https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_ATTITUDE_STATUS)
and [gimbal frame flags](https://mavlink.io/en/messages/common.html#GIMBAL_DEVICE_FLAGS).

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
