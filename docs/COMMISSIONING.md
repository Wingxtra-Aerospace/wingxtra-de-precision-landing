# Commissioning and validation record

Release candidate 1.0.0-rc.1 must be commissioned on each aircraft/camera installation. The code is packaged and software-tested; no aircraft flight-validation result is supplied. Record exact versions and objective results instead of marking the whole system flight-ready from a successful preview.

## Record before testing

Record repository commit and image digest; BlueOS and host architecture; camera model/serial, lens, focus, exposure, frame rate, delivered resolution and video path; board JSON hash and measured detection-corner sizes; calibration export, date and RMS; camera-to-body rotation and measured camera lever arm; autopilot model/firmware, parameters, MAVLink IDs and endpoint configuration. Record test date, location, operator and recovery procedure.

## Bench checks — propellers removed

1. **Startup:** with no camera/calibration/heartbeat, confirm zero LANDING_TARGET output. Configure preview and verify that no output is sent in monitor or `--dry-run`. A browser cannot enable output in a dry-run process.
2. **Camera geometry:** confirm delivered resolution exactly matches configuration. Focus and exposure must permit sharp tag edges throughout the intended envelope. Change resolution or lens profile and verify the calibration becomes invalid. Confirm no hidden crop/rotation/zoom/stabilization changes occur after reconnect or reboot.
3. **Calibration:** capture diverse views; retain the exported fit statistics. Verify an independent set of board distances and offsets after calibration. Low reprojection error does not validate print scale.
4. **Board and axes:** use a ruler/tape and fixed camera. Move the common board origin forward, right and down relative to the aircraft; reported BODY_FRD X/Y/Z must increase respectively. For the default mount, moving the target toward image top gives positive forward, and toward image right gives positive right. Check the camera lever arm only once in the autopilot configuration.
5. **Scale and common origin:** compare reported versus measured distance and horizontal offset across the intended landing envelope. Test multiple visible tags, then cover all but each usable individual tag. The reported board origin must stay consistent within the installation's accepted error. Test partially occluded, unknown, rotated, small and blurred tags. Set `min_tags` above one if the mission requires multiple-tag evidence, recognizing the resulting near-ground visibility tradeoff.
6. **Actual FC reception:** inspect raw MAVLink and the autopilot precision-landing logs/state. Confirm MAVLink 2, BODY_FRD (12), positive norm distance, finite X/Y/Z, position_valid=1, correct IDs and increasing packet sequence. Verify the autopilot accepts the target, not merely that UDP traffic exists. A LANDING_TARGET message has no destination-system field: keep the router network dedicated to the intended vehicle and avoid multi-vehicle broadcast.
7. **Loss tests:** cover the board, unplug/restart the camera, pause the network stream, remove the autopilot heartbeat feed, introduce a port conflict and stop the extension. Confirm target output stops within the configured age/heartbeat limits and does not resend the last pose. Verify reacquisition requires consecutive valid frames. Also test a camera that repeats frozen imagery; document its behavior because local receipt timestamps cannot establish exposure freshness.
8. **Latency/load:** measure exposure-to-MAVLink latency using a timed visual stimulus. Record p50/p95/max latency and actual accepted target rate under the worst expected CPU/video load, including DroneEngage if present. Check camera-driver buffering and target jitter; configure the autopilot's supported latency compensation from measurements. The example age/speed/distance limits are not a guaranteed operating envelope.
9. **Persistence:** restart the container and companion. Verify exact saved camera/board/calibration/IDs, expected startup mode, live heartbeat gating and no stale target replay. Confirm setup edits are rejected while publishing or when the last known aircraft state is armed. Resolve a latched armed state using a verified disarmed heartbeat, not by editing files in flight.

## SITL / hardware-in-the-loop

Use the target ArduCopter version. Exercise the actual LANDING_TARGET input path, target acquisition and loss, estimator settings, camera-offset handling, landing-mode entry and loss/retry behavior. Verify manual takeover and the chosen mission's fallback behavior. Software unit tests here validate protocol and service behavior; they do not substitute for this flight-stack integration test.

## Controlled flight expansion

Begin only after the recorded bench and flight-stack integration checks pass. Use a clear test area, an experienced safety pilot, immediate manual takeover and a conservative low-altitude/low-speed envelope. Expand one condition at a time: offset, altitude, lighting, wind, blur, partial board visibility and target loss. Check descent and touchdown behavior separately. Verify the chosen rangefinder-free configuration on the exact firmware if no dedicated downward rangefinder is fitted.

Define measurable limits **before** flight: maximum horizontal error, distance error, p95/max latency, minimum accepted update rate, maximum target-loss interval and the allowed operating envelope. Enter those measured limits in the configuration and aircraft record. Use the autopilot's documented approach, estimator and loss settings; the service intentionally does not invent universal flight tuning.

## Software evidence supplied

The automated suite covers rendered multiple-tag images (including the supplied original board), common-origin estimation from one tag, outlier rejection, malformed layouts, synthetic calibration recovery, duplicate calibration views, bad calibration imports, packet decoding and sequence wrap, UDP heartbeat source/expiry, DataBus framing, stale/duplicate/lost target rejection, API guards, calibration binding/persistence, relative-path hosting and a complete vision-to-UDP pipeline.

CI additionally tests the Debian/OpenCV container on native AMD64 and ARM64 and checks startup, health and BlueOS registration before exporting/pushing an image. Read the actual workflow result for the commit being installed. Pending CI, live camera, FC integration, timing and flight checks must remain explicitly pending in the aircraft record.

| Acceptance area | Result / evidence | Aircraft owner sign-off |
|---|---|---|
| Software CI for exact image commit | Attach run URL and image digest | |
| Camera identity, fixed geometry and calibration | Attach calibration and measurements | |
| Board scale, axes, distance and single/multi-tag continuity | Attach bench record | |
| Actual autopilot acceptance and parameters | Attach flight-stack logs | |
| Camera/heartbeat/target loss and reacquisition | Attach timed observations | |
| Worst-case latency, update rate and CPU load | Attach statistics | |
| Reboot and startup behavior | Attach record | |
| Controlled flight envelope and takeover | Attach flight logs and limits | |
