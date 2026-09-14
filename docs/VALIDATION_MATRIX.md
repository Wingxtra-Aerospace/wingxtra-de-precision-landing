# Validation and acceptance matrix

Last reviewed: 2026-09-14. This is the planned acceptance suite for the new work. Existing unit/browser/container evidence is recorded separately in [PROJECT_STATUS.md](PROJECT_STATUS.md). **No new scenario below is claimed passed.**

Use distinct evidence stages: automated geometry/protocol tests, SITL with the intended firmware/applet, integrated bench/HIL, and controlled flight. A software test does not stand in for a physical test. Numeric limits come from R03/O03 and must be fixed before qualification.

| Test ID | Scenario | Required observable result | Stage / task |
|---|---|---|---|
| T01 | Fixed camera with no gimbal connected or messages present | Correct board-origin output; no gimbal dependency. Existing calibration/configuration survives supported migration. | Automated + bench / F04–F05 |
| T02 | Multi-tag board, single-tag visibility, outliers, scale and planar ambiguity | Correct common origin and declared error bounds; bad fits/scale mismatches diagnosed; no jump to whichever tag is visible. | Automated + measured bench / F05 |
| T03 | Known forward/right/down offsets and sensor lever arms | Correct signs, reference point and metric distance; no duplicate offset/orientation correction in companion and FC. | Automated + FC reception / F02, G03 |
| T04 | Missing/repeated/stale frames, telemetry backlog, camera stop/reconnect and invalid calibration | No invalid measurement refresh or fabricated zero target; useful diagnostics and tested reacquisition. | Regression + integrated bench / F04–F05 |
| T05 | Aircraft and pad stationary; move gimbal through its allowed range | Reported target position in aircraft coordinates remains constant within agreed error; optical-centre movement is accounted for. | Geometry tests + measured bench / G03 |
| T06 | Tilt/yaw aircraft while gimbal stabilises; yaw follow/lock and alternate flag conventions | Correct BODY_FRD vectors; reconstructed ground target remains fixed. Test axis swaps, boresight, quaternion sign and singular attitudes. | Automated + bench/HIL / G01–G03 |
| T07 | Delayed, out-of-order or lost attitude; mismatched clocks, wrong device, unhealthy gimbal, stream freeze | Invalid observations rejected, freshness expires correctly, no fixed-mode fallback; residual undetectable video failure documented. | Failure injection + bench / G01–G05 |
| T08 | Gimbal commands, mechanical limits, settling, GCS/mission/DroneEngage interference and operator override | Exactly one control owner; measured readiness required; override and release work; no unauthorised descent from an acknowledgment alone. | SITL + device bench / G04, F03 |
| T09 | QLOITER precision hold, QLAND, QRTL and AUTO VTOL landing | Correct activation and navigation updates in intended phases; no unintended corrections during fixed-wing approach, transition or abort. | Version-matched SITL + flight / F05, Q01 |
| T10 | Excess target distance, unavailable AHRS/location, failed waypoint update and Lua callback fault | Reject before changing navigation; no crash loop or stale permission; limits and error outcomes logged. | Lua regressions + SITL / F02 |
| T11 | No acquisition, mid-descent target loss, companion kill/reboot, gimbal status loss and applet failure | FC follows the explicitly approved recovery policy even without companion assistance; account for estimator retention after messages stop. | SITL + bench/HIL before flight / F03, Q01 |
| T12 | Vision-only range and rangefinder-equipped variants; final correction cutoff | Only declared sensors required; slant range not used as vertical height; invalid height/loss and touchdown transitions follow policy. | SITL + measured bench + flight / F03, Q01 |
| T13 | CM4 ARM64 BlueOS cold start, camera device ownership, TELEM2 routing, DroneEngage, power and cooling | Repeatable startup and routing; budgets met under intended concurrent load; no serial/device contention, resource exhaustion or unexplained throttling. | Integrated bench / F05, G06 |
| T14 | Extension/applet version mismatch, configuration migration, disabling old applet and rollback | Mismatch visible and handled by the contract; one applet/publisher; calibrated working configuration recoverable. | Packaging + bench / L01 |
| T15 | Declared aircraft landing envelope and operational recovery cases | Measured landing-error statistics and all failures meet predeclared acceptance; field evidence identifies exact software/hardware/settings. | Controlled flight / V02–V03, Q02–Q03 |
| T16 | Landmark comparison, when supplied | Fair configuration/scale/timing comparison; differences reproduced against known geometry; unsupported conclusions clearly excluded. | Replay + available bench evidence / REF01 |

## Evidence record for each execution

Record test ID and scope; date and responsible tester; extension commit/image digest; applet version/hash and upstream revision; FC firmware/build; hardware models/firmware; camera/board/calibration/configuration hashes; stimulus; expected result and numerical threshold; actual measurements; raw evidence location/hash; pass/fail/not-run result; anomalies and corrective tasks.

Keep raw flight data, real camera calibration, credentials and proprietary Landmark files outside the public source tree. Reference an approved persistent location and checksum. A screenshot of a successful UI message or GitHub status is not sufficient evidence of aircraft response.

For flight results, report unsuccessful attempts and distributions of error, not only the best landing. When code/firmware/optics/settings change, identify which evidence remains applicable and which must be repeated. Update the work register and progress history at the same time.

## Qualification scope template

| Field | Required value before acceptance |
|---|---|
| Aircraft and FC | Model, physical configuration, firmware/build and parameters |
| Companion | CM4/baseboard revision, host/BlueOS versions, extension digest |
| Camera/gimbal | Model, firmware, mounting/offsets, optics, video path and mode |
| Applet | Installed filename, version/hash, upstream provenance and supported modes |
| Landing target | Board definition/hash and measured physical dimensions |
| Envelope | Range, light, motion, approach/descent and final correction limits |
| Evidence | Applicable test IDs, results, raw logs and unresolved restrictions |
| Acceptance | Named Wingxtra authority, date and any conditions |

Leave unknown values explicitly unresolved. Qualification of one fixed camera or gimbal does not qualify another automatically.
