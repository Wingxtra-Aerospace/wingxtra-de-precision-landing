# Decisions and unresolved inputs

Last reviewed: 2026-09-14. Accepted architectural direction is not evidence of implementation or flight qualification. The latest explicit user instruction governs work scope.

## Decisions

| ID | Date | State | Decision and consequence |
|---|---|---|---|
| D01 | 2026-09-14 | Accepted direction | One shared vision/output core with explicit fixed-camera and gimbal-camera modes. Fixed mode must remain independent of gimbal telemetry; failure must not silently change modes. |
| D02 | 2026-09-14 | Accepted direction | Maintain a small Wingxtra QuadPlane applet adaptation in this repository. Keep vision/geometry on the companion and flight-control supervision on the FC. Pin upstream and review licensing before copying/releasing code. |
| D03 | 2026-09-14 | Accepted sequence | Validate fixed-camera integration first, then one gimbal in downward operation. Active search/tracking is deferred. |
| D04 | 2026-09-14 | User selected | CM4 8GB RAM / 32GB eMMC with Holybro Pixhawk 6X CM4 baseboard. This selects hardware; exact software/camera compatibility and performance remain unverified. |
| D05 | 2026-09-14 | Accepted constraint | Preserve a vision-derived target-distance path without an implicit additional rangefinder requirement. The aircraft's own navigation/altitude solution is still required. |
| D06 | 2026-09-14 | Current work scope | Create and maintain the plan/tracker now. Do not implement gimbal support or the new applet until a subsequent user instruction authorises it. Record that instruction when it occurs; do not treat this as a permanent prohibition. |
| D07 | 2026-09-14 | Tracking direction | Update task status/evidence with each meaningful change. Use PR events to reconcile review/merge progress, with no autonomous flight-code changes, deployments or merges. |
| D08 | 2026-09-14 | Accepted boundary | Keep the current BODY_FRD position-output interface. Specify reference point, offsets, timing and downstream compensation before adding dynamic geometry. No gimbal quaternion in the target-orientation field. |

## Open decisions and inputs

| ID | Required input / decision | Responsible role | Blocks | Resolution record required |
|---|---|---|---|---|
| O01 | Exact ArduPlane and intended ArduCopter builds; Pixhawk revision; scripting/precland features; BlueOS and ARM64 host versions | Integration | R01, F01, hardware tests | Versions/hashes, build options and verified Lua bindings. If Copter is out of initial scope, record that explicitly. |
| O02 | Fixed camera and first gimbal model, firmware, lens, stream format and control/feedback protocol | Integration | R02; affected camera path | Capability report including actual attitude, timestamps, flags, IDs and optical geometry. A brand name alone is insufficient. |
| O03 | Landing accuracy limits, acquisition/descent envelope, light/wind/motion conditions and resource/timing budgets | Product + Flight test | R03; qualification | Numeric thresholds, measurement method and required repetitions. No assumed centimetre/FPS claims. |
| O04 | Acquisition timeout, target-loss response, operator override, transition/abort handling and final correction cutoff | Product + Flight test | R04, F03, G04 | Explicit state table for each intended mode; response when the CM4 or applet fails completely. |
| O05 | Camera exposure timing, gimbal/FC clock mapping, allowed interpolation/latency and unobservable frozen-frame limitations | Engineering | R05, G02 | Timing contract and measured error budget. Receipt timestamps alone do not settle this. |
| O06 | Sensor reference point and gimbal optical-centre movement; camera/FC offset settings and calibration migration | Engineering + Integration | R05, G03 | Transform diagrams/equations, measured offsets and proof that compensation is applied once. |
| O07 | Rangefinder-equipped versus vision-only deployment and the applet's altitude cutoff | Product + Integration | R04–R05, F03 | Supported variants and fallback behaviour; distinguish slant range from vertical height. |
| O08 | Proposed health/readiness channel between CM4 and FC | Engineering | R05, F03, G05 | Version, source identity, expiry, reboot handling and interpretation of missing data. Finalise before coding. |
| O09 | Distribution/licensing of the upstream-derived applet and reference datasets | Engineering/release owner | F01, L01 | Preserve upstream provenance/licence; review intended distribution. No automatic MIT relicensing or inclusion of proprietary reference files. |
| O10 | Landmark source/image availability and successful reference recordings | User + Integration | REF01 only | Inventory, source availability, configuration and limits of comparison. |

## Change procedure

When resolving an open item, retain its ID, date, selected option, reason, evidence and affected task/test IDs. Mark a superseded decision as superseded and link its replacement; do not overwrite history. Reopen affected acceptance when requirements, firmware, camera geometry, timing or recovery behaviour changes. Do not infer user approval of a new operating policy from a proposed plan or a passing CI run.
