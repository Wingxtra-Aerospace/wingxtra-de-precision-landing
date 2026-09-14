# Wingxtra precision landing: project status

Owner: Wingxtra Aerospace Ltd. · Last reviewed: 2026-09-14

**Current scope: planning and tracking. The user has not yet authorised implementation of the new gimbal support or Wingxtra QuadPlane applet.** A later explicit implementation instruction can change this scope; record it in the decision log. Existing software remains a release candidate.

This is the authoritative progress register. Read the [development plan](DEVELOPMENT_PLAN.md), [decisions and open questions](DECISION_LOG.md), [validation matrix](VALIDATION_MATRIX.md) and [progress history](PROGRESS_LOG.md) alongside it. The old [prototype milestones](MILESTONES.md) are historical.

## Verified starting point

| Item | Evidence and scope |
|---|---|
| Merged source baseline | `e07fd2fefbc450313972bae3f133cf315afc0870`, merge of [PR #34](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/34). Its complete tree matches tested implementation `9402aab7f5e3448fe99bcb867a7588412521bb46`. |
| Automated evidence | [PR #34 workflow 34795056753](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34795056753) reports success for that implementation. The review records 70 Python tests, browser checks, native ARM64/AMD64 container validation and packaging. This is historical evidence for that tree, not a claim about every future commit. |
| Candidate version | `1.0.0-rc.2`. Installation must identify the tested commit/image, not an assumed latest tag. |
| Selected hardware | User selected CM4 8GB RAM / 32GB eMMC with Holybro Pixhawk 6X CM4 baseboard. Selection is confirmed; operation of this assembly with Wingxtra is not yet verified. |
| Flight qualification | None recorded for Wingxtra. No physical-camera benchmark, completed Wingxtra SITL landing or aircraft landing was available during the software reviews. |
| Reference system | User reports successful Landmark operation and intends to supply its memory-card contents. The files have not been supplied or examined. |

## Status rules

- **DONE:** the named deliverable meets its acceptance criteria; code/document changes are merged where applicable, with evidence. A software task marked done is not a flight qualification.
- **IN REVIEW:** a concrete deliverable exists and is awaiting review/merge or acceptance.
- **IN PROGRESS:** work has actually started. A proposal alone does not qualify.
- **PLANNED:** work is defined but has not started. Check dependencies and the current user-authorised scope before starting.
- **BLOCKED:** a named missing input or prerequisite prevents the task from proceeding.
- **DEFERRED:** outside the initial delivery; requires a separate decision to activate.

Do not invent percentage completion from task counts. Implementation, automated tests, SITL, bench tests and flight qualification are separate evidence levels. When a change invalidates evidence, reopen the affected task and record why.

## Completed baseline deliverables

| ID | Deliverable | Status | Evidence / remaining boundary |
|---|---|---|---|
| B01 | Calibrated multi-tag board-origin estimation | DONE | [PR #32](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/32); rendered-image tests. Physical scale, optics and operating envelope need field measurements. |
| B02 | Fixed-mount BODY_FRD position output with PnP distance | DONE | [Encoder](../src/wingxtra_pl/mavlink_out/udp.py); decoded-message tests. Dynamic gimbal rotation is absent. |
| B03 | Calibration/setup UI and calibration identity checks | DONE | PR #32 and [second review](SECOND_REVIEW.md); numerical and browser checks. Aircraft calibration remains required. |
| B04 | RTSP/MJPEG/V4L2 adapters and native Picamera2 path | DONE | [Installation guide](BLUEOS_INSTALL.md); implementation present. No blanket camera-driver or hardware compatibility claim. |
| B05 | UDP routing, heartbeat freshness and rejection of invalid measurements | DONE | [PR #33](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/33), including queue/backlog and armed-state regressions. Live vehicle routing remains unverified. |
| B06 | BlueOS ARM64/AMD64 candidate packaging and metadata | DONE | PR #34 and successful workflow above. ARMv7, direct CSI inside the generic image and CM4 commissioning are not covered. |
| B07 | Gimbal / QuadPlane source review | DONE | Findings and source links in [development plan](DEVELOPMENT_PLAN.md#source-review-findings). Review identifies required changes; it does not implement them. |
| B08 | Companion/baseboard selection | DONE | User confirmation on 2026-09-14. Exact camera, gimbal and firmware versions remain open. |

## Delivery milestones

| Milestone | Scope | Current state | Exit / dependency |
|---|---|---|---|
| M0 | Living plan and tracking workflow | IN REVIEW | P01–P02; planning PR reviewed and merged, update mechanism recorded. |
| M1 | Requirements, compatibility and interface contracts | BLOCKED | R01–R05. Gimbal-specific unknowns must not prevent unrelated fixed-camera planning. |
| M2 | Fixed-camera QuadPlane integration baseline | PLANNED | F01–F05; fixed-camera SITL/bench acceptance, before qualification. |
| M3 | Fixed-camera aircraft qualification | PLANNED | V01–V03; depends on M2 and approved test envelope. |
| M4 | First gimbal in downward landing operation | PLANNED | G01–G06; depends on M2 and gimbal-specific M1 decisions. May be developed while fixed-camera qualification proceeds once authorised. |
| M5 | Gimbal integration and aircraft qualification | PLANNED | Q01–Q03; depends on M3 and M4, with fixed-camera regression evidence. |
| M6 | Reproducible releases and ongoing maintenance | PLANNED | L01–L04; qualify each supported combination separately. Maintenance continues after release. |
| M7 | Active gimbal search / tracking | DEFERRED | X01; separate operational need and design review. |

## Work register

Owner roles are proposed responsibilities, not assignments to named staff. Engineering = implementation/review; Integration = aircraft/firmware/camera setup; Flight test = Wingxtra's authorised test team; Product = Wingxtra's operational decisions.

| ID | Task / owner role | Status | Dependency or next action | Completion evidence |
|---|---|---|---|---|
| P01 | Publish plan, tracker, decisions and test matrix / Engineering | IN REVIEW | Planning branch `codex/precision-landing-roadmap`; link PR in progress history | Merged documents; scope and links checked |
| P02 | Establish updates during work and on PR events / Engineering | IN PROGRESS | Repository instructions, PR template and external PR watcher | Confirm actual watcher result; document event limits |
| R01 | Pin ArduPlane/ArduCopter, BlueOS, host OS and upstream applet / Integration | BLOCKED | Need intended firmware versions and exact build capabilities | Compatibility record with immutable references, Lua/precland availability and mode support |
| R02 | Identify cameras, gimbal, feedback and video interfaces / Integration | BLOCKED | Need model/SKU/firmware and control interface | Separate fixed/gimbal capability records; verify feedback semantics and camera geometry |
| R03 | Define accuracy, range, latency and resource budgets / Product + Engineering | BLOCKED | Need operating envelope and acceptance targets | Numeric pass/fail limits; no unspecified thresholds at qualification |
| R04 | Decide acquisition, target-loss, override and touchdown policy / Product + Flight test | BLOCKED | Resolve O04 in decision log | State/transition table, authority and fallback policy for every intended mode |
| R05 | Finalise coordinate, timing, health and version contracts / Engineering | PLANNED | R01–R04 for the affected camera path | Reviewed interfaces and migration design; camera offsets applied once |
| REF01 | Compare Landmark with Wingxtra / Engineering | BLOCKED | Waiting for user-supplied files, settings and optional successful logs | Read-only review and reproducible comparisons; source/binary limitations recorded. Does not block independent Wingxtra development. |
| F01 | Vendor a versioned Wingxtra QuadPlane applet / Engineering | PLANNED | R01, R04, R05; implementation authorisation | Upstream revision, licence/provenance, change list and loading/version evidence |
| F02 | Correct acceptance order and robust applet guards / Engineering | PLANNED | F01 | Cutoffs and nil/health checks before navigation changes; update-call failures handled; regression tests |
| F03 | Add flight-controller readiness and loss supervision / Engineering | PLANNED | R04–R05, F01 | Defined expiry, restart and operator-override behaviour, including total companion failure |
| F04 | Preserve fixed-camera operation and introduce explicit camera modes / Engineering | PLANNED | R05 | Fixed mode requires no gimbal telemetry; migration preserves existing configuration; no automatic mode fallback |
| F05 | Commission fixed camera on CM4/BlueOS/Pixhawk and simulate intended modes / Integration | PLANNED | F02–F04, R01–R03 | T01–T04, T08–T14 in validation matrix; measured load, latency, power and routing |
| V01 | Prepare fixed-camera flight test and recovery procedure / Flight test | PLANNED | M2, R03–R04 | Approved envelope, locations, operator authority and pass/fail criteria |
| V02 | Perform and analyse controlled fixed-camera flights / Flight test | PLANNED | V01 | Raw logs/video references, configuration hashes, measured accuracy and all failures retained |
| V03 | Qualify a named fixed-camera aircraft combination / Product + Flight test | PLANNED | V02 | Signed/attributed acceptance for that exact combination; limitations recorded |
| G01 | Implement one gimbal capability/telemetry adapter / Engineering | PLANNED | R02/R05 gimbal decisions, M2 | Identity, frame flags, normalised orientation, device health and freshness tests |
| G02 | Add frame-to-attitude time alignment / Engineering | PLANNED | G01, R03/R05 | Capture-time mapping or bounded measured delay; history interpolation; stale/unsynchronised data rejected |
| G03 | Implement dynamic target transformation and lever-arm handling / Engineering | PLANNED | G01–G02, R05 | Known-pose tests, offset convention, BODY_FRD output and no double compensation |
| G04 | Add landing pointing and control ownership / Engineering | PLANNED | G01, R04, F03 | Commanded vs measured position distinguished; limits/settling/override/release tested |
| G05 | Add gimbal readiness, UI diagnostics and calibration-profile checks / Engineering | PLANNED | G02–G04 | No output on missing/invalid feedback, changed zoom/crop or wrong device; visible reason codes |
| G06 | Benchmark and regression-test both modes on CM4 / Integration | PLANNED | G05, F05 | Resource and timing budgets met with intended BlueOS/DroneEngage services; fixed mode still passes |
| Q01 | Run QuadPlane/gimbal SITL and integrated bench/HIL scenarios / Integration | PLANNED | M4, R04 | All applicable validation-matrix cases; controlled failure injection and release evidence |
| Q02 | Conduct controlled gimbal flight campaign / Flight test | PLANNED | Q01, V03 | Measurements and logs for declared envelope; failures and corrective actions retained |
| Q03 | Qualify the first gimbal/aircraft combination / Product + Flight test | PLANNED | Q02 | Combination-specific acceptance; no inferred support for other gimbals |
| L01 | Package matched extension/applet releases and rollback / Engineering | PLANNED | Applicable mode's integration evidence | Version manifest, image digest, applet hash, configuration migration, licence notices and tested rollback |
| L02 | Publish commissioning and support matrix / Integration | PLANNED | Applicable qualification evidence | Separate implemented, simulated, bench-tested and flight-qualified columns |
| L03 | Establish upstream-change and dependency regression process / Engineering | PLANNED | First supported release | Named maintenance responsibility and required checks after changes; remains ongoing |
| L04 | Maintain progress and evidence through releases / Engineering | PLANNED | P01–P02 | Same-change tracker updates, decision history and reopening invalidated acceptance; ongoing |
| X01 | Evaluate active gimbal search/tracking / Product + Engineering | DEFERRED | M5 and a separate scope decision | Requirements, feasibility and new qualification plan before implementation |

## Immediate next actions

1. Review and merge the planning deliverable; retain the implementation hold until the user changes it.
2. Record exact flight firmware and fixed-camera/gimbal models when available (R01–R02).
3. Agree measurable landing requirements and failure behaviour (R03–R04).
4. Add Landmark evidence when the card arrives; continue to distinguish that system's success from Wingxtra qualification.

There are no committed calendar delivery dates. Estimate effort after requirements and hardware access are known; record changes without erasing earlier estimates or decisions.
