# Architecture and failure behavior

`camera.py` continuously drains one live source into a single latest-frame slot. Each locally received frame has a monotonic timestamp, Unix microsecond timestamp and unique sequence. The detector processes each sequence once. OpenCV/Picamera2 imports are isolated from optional hardware.

`landing_target_layout.py` validates unique tag36h11 IDs and finite square corners on a common z=0 board plane. Coordinates are metres. The four corners retain the tag's intrinsic corner order and the shared board origin. White margins and print metadata are not measurement dimensions.

`vision_multitag.py` detects all visible known tags above the pixel-size threshold. Multiple tags use RANSAC, retaining only complete inlier tags; contradictory multi-tag evidence cannot silently collapse to a single tag. A single visible tag is independently supported. IPPE evaluates planar pose solutions and selects a positive-depth minimum-reprojection-error solution. Translation is the board origin in camera coordinates, including when that origin lies outside the currently visible tag.

`tracking.py` applies distance, finite-vector, downward-direction, reprojection, tag-count, monotonic timestamp, frame age and relative-motion gates. Rejected images never refresh the last accepted position/time. A gap resets the motion reference, and multiple consecutive good frames are needed to reacquire. There is no undocumented EMA filter adding lag, and no retransmission loop for old poses.

`mavlink_out/udp.py` creates MAVLink 2 LANDING_TARGET messages with persistent sequence numbers. Position is camera-relative translation rotated into BODY_FRD. Distance is its positive Euclidean norm. The quaternion is a valid identity value; this service does not claim to report landing-pad attitude. ArduPilot's precision-landing position backend uses the position vector, not that quaternion. The sender learns its router peer from the configured ArduPilot system/component-1 heartbeat and rejects unrelated systems, components and hosts. It sends no GCS heartbeat, arm, mode or parameter command.

`service.py` coordinates the camera, calibration, tracker, router and output modes under a lock. Each target packet is produced only from a fresh accepted image while publish mode is enabled and a valid heartbeat is recent. A processing exception disables publishing. `--dry-run` cannot be overridden through the interface. Last-known armed state stays latched through heartbeat loss, blocking setup edits until a disarmed heartbeat arrives. This is an operational guard, not a flight-controller arming interlock; the autopilot remains responsible for aircraft safety.

The UI is static local HTML/CSS/JavaScript served by FastAPI. All asset and API requests are relative, supporting BlueOS's extensionv2 prefix. Calibration uses the same camera frames as landing, refuses duplicate/nearly identical views, checks spatial/scale/tilt diversity, evaluates numerical RMS and stores finite checked intrinsics. Persistent files use atomic replacement. Logs are JSON lines, capped at 10 MB plus three rotated backups. Browser preview encoding is limited to 5 Hz and 960 pixels wide; the detector uses original-size images.

## Output modes

| Mode | Camera / preview | Target measurements |
|---|---|---|
| Stopped | Off | None |
| Monitor | On | Computed, never sent |
| Publish | On | Sent only when calibration, tracking and heartbeat checks pass |
| Calibration session | On in monitor mode | None; publishing is blocked |

Startup defaults to stopped. An operator can save monitor or publish-on-restart behavior after commissioning. Startup never bypasses calibration checks or restores a previously measured target. Failure to bind the MAVLink UDP port is visible in diagnostics and blocks output rather than silently sharing the port.

## Explicit limits

The application is not a flight controller. It does not replace EKF/navigation, altitude estimation, landing-mode management, pilot takeover or loss-of-target policy. PnP distance can remove the measurement's dependency on a separate rangefinder; it cannot make an aircraft fly without an altitude solution.

Local decode timestamps bound processing age, not network/exposure latency. A frozen camera feed that keeps emitting newly encoded frames is not reliably distinguishable from a stationary scene. Measure video latency and assess camera failure behavior during commissioning. USB/CSI driver hangs can require an extension restart; the latest-frame age gate stops target output while acquisition is blocked.

The generic image is ARM64/AMD64, CPU OpenCV, pinhole/radial-tangential calibration and a rigid downward camera. Fisheye models, moving gimbals, moving-pad velocity prediction, offboard cloud processing, 32-bit ARM, PX4 and direct CSI-in-container operation are not validated by this release.
