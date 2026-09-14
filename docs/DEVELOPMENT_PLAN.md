# Fixed-camera and gimbal precision-landing development plan

Wingxtra Aerospace Ltd. · Planning baseline: 2026-09-14

Progress is maintained in [PROJECT_STATUS.md](PROJECT_STATUS.md). The user authorised implementation of selectable fixed/gimbal modes and the Wingxtra QuadPlane applet on 2026-09-14. That authorisation covers reviewable source work, not aircraft deployment or flight acceptance.

## Objectives and boundaries

Support a shared calibrated multi-tag vision engine with explicit fixed-camera and gimbal-camera modes. Keep the existing fixed-camera path usable without gimbal hardware or feedback. Maintain a Wingxtra adaptation of the QuadPlane applet, matched to identified ArduPlane releases. Qualify each camera/firmware/aircraft combination using evidence rather than a general “flight ready” label.

First gimbal scope: controlled downward landing operation with compensation for stabilisation and verified orientation. Active searching/tracking, moving-platform landing, additional gimbal families, fisheye optics and autonomous zoom changes are separate extensions of scope. Vision supplies target distance; a working aircraft altitude/navigation solution remains necessary. A downward rangefinder must not become an undocumented requirement of the vision-only configuration.

Deployment target selected by the user: CM4 8GB / 32GB eMMC on the Holybro Pixhawk 6X CM4 baseboard. The current extension is ARM64/AMD64; validate a suitable 64-bit host/BlueOS installation on this specific board. BlueOS owns the physical FC link, normally the internal TELEM2 connection. Wingxtra and DroneEngage use distinct router endpoints. Assign one owner to each physical camera and one precision-landing publisher to the aircraft.

## Architecture

| Layer | Fixed camera | Gimbal camera |
|---|---|---|
| Acquisition/calibration | Existing supported video adapters; matching resolution and optics | Same image contract; additionally identify gimbal/camera, geometry profile and capture timing |
| Vision | Calibrated detection of the common physical board origin | Same estimator and physical board definition |
| Orientation | Calibrated constant camera-to-body transform | Constant optical alignment combined with measured, time-aligned gimbal/aircraft orientation |
| Acceptance | Image, pose, telemetry and configured quality checks | Same checks plus device health, attitude freshness, frame semantics, timing and pointing readiness |
| Output | MAVLink 2 BODY_FRD target position and positive distance | Same output contract, with agreed reference-point/lever-arm treatment |
| Vehicle control | Native Copter precision landing or Wingxtra QuadPlane applet | Same controller boundary; gimbal readiness participates in landing supervision |

Keep image processing on the CM4. Keep aircraft descent, landing-target updates and companion-failure response under flight-controller authority. Implement gimbal commands through one identified manager/driver and a documented ownership policy. Do not allow UI, mission, DroneEngage and a second service to issue competing gimbal commands.

### Coordinate contract — R05, G03

- Name every coordinate frame, axis convention, quaternion convention and reference point. Camera optical axes and gimbal device axes are not interchangeable.
- Fixed-camera mode retains its calibrated constant transformation. Gimbal mode computes the transformation for each image without rewriting persisted installation calibration during flight.
- Handle aircraft-relative versus Earth-referenced gimbal yaw flags, roll/pitch stabilisation semantics, boresight calibration and device-specific conventions. Do not assume the reported quaternion is already a full camera-to-body rotation. Vehicle-heading yaw does not supply aircraft roll/pitch compensation: compose time-aligned aircraft attitude with the appropriate horizon/heading frame, and validate tilted-aircraft cases (T06).
- Keep BODY_FRD X/Y/Z and `distance = norm(position)` at the output boundary, with `position_valid=1`. `LANDING_TARGET.q` describes target orientation; placing a gimbal quaternion there does not rotate X/Y/Z.
- The current output vector originates at the camera and relies on the FC's configured camera offset. A gimbal can move the optical centre. Decide whether to compensate to a fixed reference such as the pivot or aircraft origin; then match FC offset settings and migration to that choice. Include the offset once, not in both components.
- Match companion transformation timing to the FC's attitude/latency handling. Do not compensate the same rotation, displacement or delay twice.

### Timing and geometry — R03, G02, G05

Current frame timestamps record local receipt/decode, not proven exposure time. Establish clock mapping and an attitude history, or demonstrate a bounded latency model on the chosen camera. Reject observations that cannot satisfy the agreed timing-error budget. Fresh UDP arrival does not prove a gimbal device's orientation estimate is fresh. Validate device-clock progression per selected source; repeated or reordered timestamps must not renew readiness. D10 records the implemented startup/progression/wrap policy and T07 covers its software regressions. O05/R05 still require measured clock/exposure mapping and device evidence; receipt-time matching alone does not settle that contract.

Measure end-to-end exposure-to-target delay under the intended video format/resolution and concurrent load. Bound the resulting position error using expected aircraft/gimbal motion and landing range. Decide telemetry rates from that budget; do not assume a nominal frame rate or 1 Hz attitude stream is sufficient. Repeatedly encoded frozen video is a separate limitation: document and test what the selected hardware can detect, and the remaining operational response.

Lock or verify zoom, focus, crop, digital stabilisation and image rotation against a calibrated profile. A reconnect must not silently select different optics, stream geometry or device identity. Test printed board scale and detection-corner coordinates physically. Low reprojection error alone does not prove correct distance.

### Gimbal control and readiness — R04, G04–G05

Define an explicit sequence: available/identified, requested landing orientation, moving, settled, target acquisition, ready, tracking, lost/stale, recovery or operator override. State names are design labels, not yet an implemented API.

Command success is not evidence of achieved orientation. Use actual feedback, failure flags and settling criteria. Do not publish in gimbal mode with unknown/missing attitude and do not silently fall back to fixed mode. Preserve operator override and define how ownership is released after landing, abort or process restart.

Recognise actual VTOL landing phases. QRTL includes phases other than vertical descent; abort/transition states must have explicit behaviour. Acquire and establish readiness before relying on precision corrections, rather than assuming a mode change alone establishes readiness.

### Wingxtra QuadPlane applet — F01–F03

The initial plan proposed `autopilot/quadplane/wingxtra_precland.lua`. [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36) merged [`applets/wingxtra_plane_precland.lua`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/4819cebf823f573c738f343304556fa85ffdb88d/applets/wingxtra_plane_precland.lua), with adjacent documentation and GPL provenance. It runs on the Pixhawk's `APM/scripts`, not on the companion's eMMC. Verify installation so the upstream and Wingxtra controllers cannot both run unintentionally.

The PR pins upstream commit `9456449a442617b2af1c3132b64c3120f1694583` and preserves GPL-3.0-or-later notices. The intended firmware/build and Lua bindings still require R01 validation; retain provenance and track local changes. The current extension is MIT licensed; do not relabel upstream-derived GPL code as MIT or assume folder separation resolves distribution obligations. Review the planned distribution and record the conclusion before releasing the combined package.

The applet should:

- Validate health, location availability, allowed flight phase, range/distance cutoffs and limits before changing navigation targets.
- Check the result of navigation-update operations, guard unavailable values and handle callback failures visibly.
- Supervise readiness/expiry independently of a healthy companion process. Define the health channel, identity, restart behaviour and timeout contract; stale good status must not authorise continued corrections.
- Implement the agreed acquisition, target-loss, operator-override and final-touchdown policies. Stopping LANDING_TARGET transmission alone does not immediately stop descent or clear the FC estimator.
- Preserve the FC's flight-control authority. Use supported vehicle APIs and test the actual ArduPlane bindings. Do not assume Copter retry/descent behaviour is inherited automatically.
- Preserve a deliberately supported vision-only configuration. The upstream optional altitude cutoff uses a downward rangefinder. Any vision-based alternative must distinguish slant distance from vertical height and define loss behaviour.

An applet cannot supervise itself after the Lua engine has stopped. For that failure, demonstrate the native firmware's watchdog/fallback behaviour against the selected policy. If the required response cannot be achieved through supported APIs, raise a firmware/architecture decision and block that qualification claim; do not describe a second Lua callback as an independent guarantee.

Start with only the intended QuadPlane modes; qualify QLOITER precision hold, QLAND, QRTL and AUTO VTOL landing separately, including their activation requirements. Keep ordinary Copter operation independent of the QuadPlane applet.

## Delivery sequence and gates

| Gate | Work | Required exit evidence |
|---|---|---|
| M0 | Plan/tracker publication | Reviewable documents, update instructions and actual automation status |
| M1 | Requirements and interfaces | Exact relevant hardware/firmware, measurable budgets, frame/timing/health contracts and flight-state decisions |
| M2 | Fixed-camera baseline plus applet | Resolve reopened B01/T02 multi-tag rejection with regression evidence, then intended-mode SITL and integrated CM4/Pixhawk bench evidence; no gimbal required |
| M3 | Fixed-camera qualification | Controlled flights with measured acceptance and recorded limitations |
| M4 | First downward gimbal | One verified feedback/control adapter, timed geometry, readiness/UI and fixed-camera regressions |
| M5 | Gimbal qualification | Failure-injection SITL/bench results followed by controlled flights; combination-specific acceptance |
| M6 | Release/support | Matched versions, provenance, configuration migration, rollback and a capability matrix tied to evidence |
| M7 | Optional active search/tracking | Separate requirements and scope decision; not required for initial fixed/downward-gimbal delivery |

Gimbal work may proceed after the fixed-camera integration baseline once authorised and its own inputs are known. Gimbal flight qualification requires the fixed-camera baseline to have been qualified. Landmark comparison is a useful independent reference track; waiting for its card must not unnecessarily block other work.

Use [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) for scenarios and evidence requirements. Numeric acceptance targets are decided in R03, not invented during testing. A camera or firmware change can invalidate earlier evidence and must reopen the affected work.

## Landmark comparison — REF01

Inspect a copy of supplied files/image without altering the working original. Inventory source or binaries, camera settings/calibration, tag-board scale, startup services, dependencies, parameters and any successful test logs. Preserve credentials and proprietary code outside this source repository.

The first supplied boot archive is inventoried in [LMBOOT-001](LANDMARK_REFERENCE_REVIEW.md). It provides calibration and board definitions, but no located Landmark application or reference recordings. This partial comparison exposed a reproducible Wingxtra multi-tag rejection and reopened B01/T02. Correct that shared-core defect with planar-board regressions while retaining whole-tag outlier protection; validate both declared OpenCV environments before claiming it resolved. Missing Landmark source does not prevent that correction. Physical layout units, active board, camera identity and calibration migration remain unverified; do not silently alter board scale or bypass calibration checks.

Where possible, replay common recorded observations with the correct configuration for each system and compare measured target vectors, timing, acquisition/loss behaviour and emitted messages. Reproduce confirmed differences as Wingxtra regression cases with known geometry. A working reference is not an oracle for every scenario; matching one flight or copying parameters does not establish equivalence. If source is unavailable, state the limits of behavioural/binary comparison. Do not redistribute Landmark software or datasets without the necessary rights.

## Source-review findings

Initial source review on 2026-09-14. These findings describe the starting implementations; PR #36's corrections are tracked in PROJECT_STATUS. The upstream links below follow moving branches; the vendored applet revision is pinned above, while installed-firmware compatibility remains open under R01.

- The [BlueOS application](https://github.com/rmackay9/blueos-precision-landing/blob/main/app/main.py) checks reported gimbal orientation against a downward quaternion with approximately 10° tolerance. It does not command pointing and sends targets when attitude retrieval fails. Its [MAVLink module](https://github.com/rmackay9/blueos-precision-landing/blob/main/app/mavlink_interface.py) sends LOCAL_FRD angles with zero distance, without applying the measured gimbal orientation to every image.
- The [upstream QuadPlane applet](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_Scripting/applets/plane_precland.lua) consumes the common precland estimate. It checks `PLND_DIST_CUTOFF` after updating the waypoint, returns on target loss and requires downward rangefinder data when its optional altitude cutoff is enabled. These are review findings to address/test, not fixes already made.
- Current [ArduPilot MAVLink backend](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AC_PrecLand/AC_PrecLand_MAVLink.cpp) and [frontend](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AC_PrecLand/AC_PrecLand.cpp) distinguish BODY_FRD and LOCAL_FRD. Installed firmware may differ. Keep our sensor conversion before controller use and avoid assuming that merely adding Lua corrects camera geometry.
- Wingxtra's pre-PR-36 baseline at `e07fd2fefbc450313972bae3f133cf315afc0870` used a [constant mount matrix](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/e07fd2fefbc450313972bae3f133cf315afc0870/src/wingxtra_pl/service.py); its [telemetry handling](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/e07fd2fefbc450313972bae3f133cf315afc0870/src/wingxtra_pl/mavlink_out/udp.py) recorded autopilot heartbeats without gimbal/aircraft attitude history. PR #36 added that history and dynamic conversion while preserving the fixed mode. [Architecture limitations](ARCHITECTURE_OVERVIEW.md) continue to exclude validated moving-gimbal operation.

References: [gimbal control](https://ardupilot.org/dev/docs/mavlink-gimbal-mount.html), [gimbal frame/ownership protocol](https://mavlink.io/en/services/gimbal_v2.html), [QuadPlane applet instructions](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_Scripting/applets/plane_precland.md), [upstream licence](https://github.com/ArduPilot/ardupilot/blob/master/COPYING.txt).
