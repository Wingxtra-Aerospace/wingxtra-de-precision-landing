# Wingxtra precision landing: project status

Owner: Wingxtra Aerospace Ltd. · Last reviewed: 2026-09-14

**Current scope: explicit fixed/gimbal camera modes and the Wingxtra QuadPlane applet are merged on main; their previously recorded automated checks pass. A new multi-tag pose rejection has reopened B01.** Version-matched SITL, physical bench integration, aircraft configuration, deployment and flight qualification remain unperformed and require their own evidence. The merged software remains a release candidate with an unresolved vision defect.

This is the authoritative progress register. Read the [development plan](DEVELOPMENT_PLAN.md), [decisions and open questions](DECISION_LOG.md), [validation matrix](VALIDATION_MATRIX.md) and [progress history](PROGRESS_LOG.md) alongside it. The old [prototype milestones](MILESTONES.md) are historical.

## Verified starting point

| Item | Evidence and scope |
|---|---|
| Merged source baseline | `e07fd2fefbc450313972bae3f133cf315afc0870`, merge of [PR #34](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/34). Its complete tree matches tested implementation `9402aab7f5e3448fe99bcb867a7588412521bb46`. |
| Automated evidence | [PR #34 workflow 34795056753](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34795056753) reports success for that implementation. The review records 70 Python tests, browser checks, native ARM64/AMD64 container validation and packaging. This is historical evidence for that tree, not a claim about every future commit. |
| Candidate version | `1.0.0-rc.2`. Installation must identify the tested commit/image, not an assumed latest tag. |
| Selected hardware | User selected CM4 8GB RAM / 32GB eMMC with Holybro Pixhawk 6X CM4 baseboard. Selection is confirmed; operation of this assembly with Wingxtra is not yet verified. |
| Flight qualification | None recorded for Wingxtra. No physical-camera benchmark, completed Wingxtra SITL landing or aircraft landing was available during the software reviews. |
| Reference system | User reports successful Landmark operation and has supplied a boot-partition archive. Calibration and two board layouts were inspected; no Landmark landing application, active runtime configuration or successful flight logs were located. [Restricted-input comparison and evidence](LANDMARK_REFERENCE_REVIEW.md). REF01 remains partially completed and blocked on the remaining inputs. |

## Landmark boot-data review — 2026-09-14

Inspected the supplied archive against main [`ab2f242790d324ef030602f0aa2a5bcbf940f8c5`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/ab2f242790d324ef030602f0aa2a5bcbf940f8c5). [Evidence record LMBOOT-001](LANDMARK_REFERENCE_REVIEW.md) identifies the archive and relevant files by SHA-256, records loader results and provides the synthetic reproduction recipe. This is local data/software analysis, not Landmark execution, replay of recorded images, SITL, bench or flight evidence.

- The four-tag A4 layout loads without modification. The fifteen-tag Fibonacci layout reaches the existing 5 m marker-edge guard under Wingxtra's metre interpretation; its physical scale and whether it was active remain unknown. The 3280×2464 calibration does not meet Wingxtra's schema, identity/quality metadata or current height limit. No conversion or limit change was made.
- **B01 is reopened:** at Python 3.12.14 / NumPy 2.5.3 / OpenCV 4.13.0, exact projected observations of the accepted A4 layout are rejected at synthetic camera depths 0.5 m and 1.0 m for each of three seeds. All corners are visible, at positive depth and above the existing minimum edge size. The EPNP-RANSAC prefilter rejects/discards valid corners before IPPE can solve the complete board; direct IPPE fits the same complete observations with negligible residual. Six of twelve depth/seed cases return no pose. These depths are diagnostic inputs, not declared aircraft operating limits.
- Earlier rendered-image/CI passes remain evidence for their exercised cases; they did not establish robustness for these new inputs. The shared vision core affects both camera modes. Correct B01 and add regression coverage across the declared OpenCV environments before F05/M2 acceptance; do not remove outlier rejection simply to admit this board.
- REF01/O10 remain open pending the Linux root filesystem or installed Landmark application and startup/configuration files, plus identified hardware/settings and reference observations/logs. A complete image may contain an executable without source. This archive alone cannot establish Landmark's joint-tag algorithm, range/altimeter requirements, gimbal handling or aircraft behaviour.

## Merge-integrity review — 2026-09-14

The user requested a review after resolving conflicts between PR #36 and PR #37. Main at [`d6ed94a5474ba869b15299b1d4cfa310c816cc84`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/d6ed94a5474ba869b15299b1d4cfa310c816cc84) preserves the complete PR #36 implementation. Compared with tested source `176c9e0c3b761a158b88058049c0176d6bb68fe1`, only the five tracking documents differ. Main's tree `23e7fe8f4f42aab858d56133adc263b39d32faaa` also matches the final PR #37 head `0be3fd0ed15adbe9aa94f95b011c330f5b78aab4`. No conflict markers, whitespace errors or lost runtime/applet/test changes were found.

- [Final-merge workflow 34846268164](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164), attempt 1, completed successfully at 2026-09-14 13:00:43 UTC. [Python job 103982856299](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/job/103982856299) reports **126 Python tests passed**, **12 Lua API-stub scenarios passed**, and passing lint, formatting and browser checks. Two Python dependency deprecation warnings remain.
- [AMD64 job 103983220517](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/job/103983220517) and [ARM64 job 103983220530](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/job/103983220530) pass. Their test-build layers are cached; this run freshly exercises container startup, BlueOS metadata, health and disabled output. The earlier post-merge run 34841164832 below independently executed all 126 tests on each native architecture.
- [Manifest job 103983887907](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/job/103983887907) publishes `ghcr.io/wingxtra-aerospace/wingxtra-de-precision-landing:sha-d6ed94a5474ba869b15299b1d4cfa310c816cc84`, digest `sha256:95d5316e4f9752a960cb575dbd49dbe536d70ce2c0cb0caf784f6d3af01b22e7`. Artifacts: [Python results 10347743139](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/artifacts/10347743139), [AMD64 archive 10348067713](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/artifacts/10348067713), [ARM64 archive 10347104925](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34846268164/artifacts/10347104925). Publication does not prove installation on the selected CM4.
- A fresh checkout of that main commit also passes **126 Python tests** (two dependency deprecation warnings), Ruff lint/format, JavaScript syntax and the **12 Lua API-stub scenarios** locally. This review confirms merge integrity and software validation; F02–F03, G01–G05 and all SITL/bench/flight acceptance gates remain open as scoped below.

## Merged camera/gimbal implementation

[PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36) merged on 2026-09-14 as [`4819cebf823f573c738f343304556fa85ffdb88d`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/4819cebf823f573c738f343304556fa85ffdb88d). Its tree `42cc5f3d12889773577922c3776c0217cd04cfc6` exactly matches tested source head [`176c9e0c3b761a158b88058049c0176d6bb68fe1`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/176c9e0c3b761a158b88058049c0176d6bb68fe1). The merge incorporates the corrections for both software failures reproduced at `fa363e5680e577784194b3f023f114eecf16e055`. The inspected PR records one automated COMMENTED review and no human review submission.

- G01/G03: the companion now accepts autopilot `ATTITUDE` or `ATTITUDE_QUATERNION` and composes full aircraft roll/pitch/yaw with the gimbal's declared earth/heading frame before encoding BODY_FRD. Missing, invalid or misaligned aircraft data inhibits gimbal output. Fixed mode keeps its constant transform and requires neither attitude stream.
- G02/G05: separate device clocks require progression before use; duplicates, reordered timestamps and implausible jumps cannot refresh accepted data. Bounded uint32 wrap is supported. Clock rollback does not automatically establish a new boot epoch; session reset is documented in D10. Invalid feedback clears healthy history, and multiple matching gimbals require explicit IDs.
- Local software validation: **126 Python tests pass** (two dependency deprecation warnings), including **56 camera/gimbal tests**. Four wire/service regressions fail on the earlier implementation with the expected incorrect-vector/stale-acceptance assertions and pass with this correction. Ruff lint and all 32 Python files' formatting pass.
- These two reproduced software defects are corrected in the merged implementation. G01–G05 remain IN PROGRESS because full T06/T07 bench/HIL, exposure-time mapping, camera/gimbal/firmware identification, lever-arm handling, control policy and aircraft acceptance remain outstanding. Existing downward-angle limits are preserved. This does not change aircraft settings or select a landing-loss policy.

| Current evidence | Result and boundary |
|---|---|
| [PR-head CI run 34830596708](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708), attempt 1, last updated 2026-09-14 10:00:33 UTC | Completed successfully for `176c9e0c3b761a158b88058049c0176d6bb68fe1`. This validates the exact tree later merged as `4819cebf823f573c738f343304556fa85ffdb88d`; it is software evidence, not deployment or flight qualification. |
| [Python job 103932758067](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/job/103932758067) | **126 Python tests pass**, with two dependency deprecation warnings; **12 Lua API-stub scenarios pass**. Ruff lint/format, frontend syntax/format and browser checks pass. Stubbed APIs do not validate installed firmware. |
| [AMD64 job 103933031659](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/job/103933031659) and [ARM64 job 103933031693](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/job/103933031693) | Each native Debian OpenCV test run reports **126 passed**; image builds, startup/health and disabled-output checks pass. Registry push and manifest publication are intentionally skipped for pull requests. |
| Run artifacts | [python-test-results, 10342131718](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/artifacts/10342131718); [blueos-image-amd64, 10342002551](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/artifacts/10342002551); [blueos-image-arm64, 10342471042](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708/artifacts/10342471042). Job logs and artifact metadata were inspected. The archives were not independently installed on the selected CM4. |
| [Post-merge CI run 34841164832](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832), last updated 2026-09-14 12:05:53 UTC | Completed successfully for merge `4819cebf823f573c738f343304556fa85ffdb88d`: [Python job 103966236658](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/job/103966236658), [AMD64 job 103966538527](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/job/103966538527), [ARM64 job 103966538606](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/job/103966538606) and [manifest job 103967428823](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/job/103967428823) all pass. The Python and both container runs report 126 tests; Lua stubs, browser, native builds and startup/health checks pass. |
| Post-merge artifacts | [python-test-results, 10345699451](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/artifacts/10345699451); [blueos-image-amd64, 10345879304](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/artifacts/10345879304); [blueos-image-arm64, 10345993646](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832/artifacts/10345993646). Archive SHA-256: `fc56618bc…c784`, `7b0cc7d6…ffc8`, `19bc8d24…7b3c`; full values remain in GitHub artifact metadata. |
| Published candidate manifest | The workflow pushed commit-qualified architecture tags and combined `ghcr.io/wingxtra-aerospace/wingxtra-de-precision-landing:sha-4819cebf823f573c738f343304556fa85ffdb88d`, manifest digest `sha256:f1c4de51d21dc098b99d9b00298835ee90d7f969fd2d90bffdeef8c56449a90d`. Publication is traceability evidence; no CM4 installation or deployment is claimed. |

Artifact archive digests reported by GitHub for **PR-head run 34830596708** (source `176c9e0c3b761a158b88058049c0176d6bb68fe1`), not either post-merge run, are:

| Artifact | Archive SHA-256 (not an installed image digest) |
|---|---|
| python-test-results | `2e236be746601b26191126dfb8aec0e1a56c6e5761d6bb3b4da7b3a35f1571ec` |
| blueos-image-amd64 | `50dd05ca73c689bb4965f3bc143badf62ae0d5ffbd78a6e31ded5ec3e982fcc1` |
| blueos-image-arm64 | `bec63d81cb82d810bfa4ee45b7c0656a9ca03444c0deade716bd7842ce07fcdf` |

## Earlier implementation review — PR #36

[PR #35](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/35) merged the tracker as `5194f27551b4fad534915fbdd21e4d16febb77ff`. [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36) was open, ready for review and unmerged at [`fa363e5680e577784194b3f023f114eecf16e055`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/fa363e5680e577784194b3f023f114eecf16e055). At that earlier snapshot, its implementation was present on the PR branch only.

The unused `half` assignment was removed in `e8b19575bcf404a59765b447f78ad2d0dc369ad2`. Commit `fa363e5680e577784194b3f023f114eecf16e055` removes the unused NumPy import, fixes formatting and corrects the applet's `mount:get_attitude_euler` return order. It preserves the earlier fix.

| Evidence | Result and boundary |
|---|---|
| [CI run 34827077062](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062), last updated 2026-09-14 09:20:17 UTC | Completed successfully for `fa363e5680e577784194b3f023f114eecf16e055`. This is software/container evidence for the unmerged PR. |
| [Python job 103921586156](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/job/103921586156) | Ruff lint/format, frontend syntax/format and browser checks pass; **78 Python tests pass** with two dependency deprecation warnings; **12 Lua API-stub scenarios pass**. Stubbed APIs do not validate installed firmware. |
| [AMD64 job 103921869873](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/job/103921869873) and [ARM64 job 103921869879](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/job/103921869879) | Image builds, Debian OpenCV tests and container startup/health checks pass. Registry push and the manifest job are skipped by the pull-request workflow conditions; no published release is claimed. |
| GitHub artifacts for this run | [python-test-results, 10340224686](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/artifacts/10340224686); [blueos-image-amd64, 10339988732](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/artifacts/10339988732); [blueos-image-arm64, 10340419758](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062/artifacts/10340419758). Artifact metadata and job logs were inspected; image archives were not independently installed on the selected CM4. |

**The following defects remained in that earlier tree despite passing CI.** Two automated review findings against parent `e8b19575bcf404a59765b447f78ad2d0dc369ad2` were independently checked against the earlier `fa363e5680e577784194b3f023f114eecf16e055` tree and reproduced with read-only synthetic inputs. No human review or approval was present at this snapshot.

| Affected work / test | Verified earlier blocker | Correction identified at that review |
|---|---|---|
| G01–G03 / T06; M4 | [Missing aircraft roll/pitch conversion](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36#discussion_r4003725723): `gimbal_to_body_rotation` treats heading/horizon-referenced orientation as full BODY_FRD. With a horizon-down target 2 m away and illustrative aircraft roll of 10°, it returns approximately `[0, 0, 2]` instead of `[0, 0.347296, 1.969616]` m. | Ingest time-aligned aircraft attitude, compose the complete horizon/earth-to-body rotation, and add tilted-aircraft regressions for supported yaw-frame conventions. |
| G01–G02, G05 / T07; M4 | [Nonadvancing device time refreshes stale orientation](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36#discussion_r4003725728): `time_boot_ms` is stored but not checked. Repeating device time `1234` at receive times `10` and `20` seconds still authorises the target at time `20`. | Track timestamp progression per selected device; expire cached/reordered data and define explicit reboot/wrap handling before acceptance. Preserve fixed-mode independence. |

The illustrative inputs above are diagnostic stimuli, not operating limits. That earlier CI pass did not cover these failures; the new regression evidence is recorded above. Full T06/T07 acceptance remains withheld pending the remaining integration evidence. No previously DONE gimbal task is being reopened because none was accepted. Historical B01–B08 evidence remains scoped to its original fixed-camera/software baseline. SITL, CM4/device bench tests and Wingxtra flight qualification remain unperformed.

## Status rules

- **DONE:** the named deliverable meets its acceptance criteria; code/document changes are merged where applicable, with evidence. A software task marked done is not a flight qualification.
- **IN REVIEW:** a concrete deliverable exists and is awaiting review/merge or acceptance.
- **IN PROGRESS:** work has actually started. A proposal alone does not qualify.
- **PLANNED:** work is defined but has not started. Check dependencies and the current user-authorised scope before starting.
- **BLOCKED:** a named missing input or prerequisite prevents the task from proceeding.
- **DEFERRED:** outside the initial delivery; requires a separate decision to activate.

Do not invent percentage completion from task counts. Implementation, automated tests, SITL, bench tests and flight qualification are separate evidence levels. When a change invalidates evidence, reopen the affected task and record why.

## Baseline deliverables

| ID | Deliverable | Status | Evidence / remaining boundary |
|---|---|---|---|
| B01 | Calibrated multi-tag board-origin estimation | IN PROGRESS | Reopened by [LMBOOT-001](LANDMARK_REFERENCE_REVIEW.md#synthetic-pose-rejection): valid mixed-size planar observations are rejected on OpenCV 4.13.0. Diagnosis is complete; a correction and regression tests are not implemented. [PR #32](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/32) rendered-image evidence remains valid for its original cases. Physical scale/optics/envelope acceptance remains separate. |
| B02 | Fixed-mount BODY_FRD position output with PnP distance | DONE | [Encoder](../src/wingxtra_pl/mavlink_out/udp.py); decoded-message tests. This records the fixed-camera baseline; dynamic gimbal support was added later in PR #36. |
| B03 | Calibration/setup UI and calibration identity checks | DONE | PR #32 and [second review](SECOND_REVIEW.md); numerical and browser checks. Aircraft calibration remains required. |
| B04 | RTSP/MJPEG/V4L2 adapters and native Picamera2 path | DONE | [Installation guide](BLUEOS_INSTALL.md); implementation present. No blanket camera-driver or hardware compatibility claim. |
| B05 | UDP routing, heartbeat freshness and rejection of invalid measurements | DONE | [PR #33](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/33), including queue/backlog and armed-state regressions. Live vehicle routing remains unverified. |
| B06 | BlueOS ARM64/AMD64 candidate packaging and metadata | DONE | PR #34 and successful workflow above. ARMv7, direct CSI inside the generic image and CM4 commissioning are not covered. |
| B07 | Gimbal / QuadPlane source review | DONE | Findings and source links in [development plan](DEVELOPMENT_PLAN.md#source-review-findings). Review identifies required changes; it does not implement them. |
| B08 | Companion/baseboard selection | DONE | User confirmation on 2026-09-14. Exact camera, gimbal and firmware versions remain open. |

## Delivery milestones

| Milestone | Scope | Current state | Exit / dependency |
|---|---|---|---|
| M0 | Living plan and tracking workflow | DONE | P01–P02; PR #35 merged and the first live merge reconciliation was observed. |
| M1 | Requirements, compatibility and interface contracts | BLOCKED | R01–R05. Gimbal-specific unknowns must not prevent unrelated fixed-camera planning. |
| M2 | Fixed-camera QuadPlane integration baseline | IN PROGRESS | F01/F04 are merged; reopened B01, F02–F03 and F05 SITL/bench acceptance remain. |
| M3 | Fixed-camera aircraft qualification | PLANNED | V01–V03; depends on M2 and approved test envelope. |
| M4 | First gimbal in downward landing operation | IN PROGRESS | G01–G05 have merged software implementation and T06/T07 regressions; M2, gimbal-specific M1 inputs, G06 and integrated acceptance remain required. |
| M5 | Gimbal integration and aircraft qualification | PLANNED | Q01–Q03; depends on M3 and M4, with fixed-camera regression evidence. |
| M6 | Reproducible releases and ongoing maintenance | PLANNED | L01–L04; qualify each supported combination separately. Maintenance continues after release. |
| M7 | Active gimbal search / tracking | DEFERRED | X01; separate operational need and design review. |

## Work register

Owner roles are proposed responsibilities, not assignments to named staff. Engineering = implementation/review; Integration = aircraft/firmware/camera setup; Flight test = Wingxtra's authorised test team; Product = Wingxtra's operational decisions.

| ID | Task / owner role | Status | Dependency or next action | Completion evidence |
|---|---|---|---|---|
| P01 | Publish plan, tracker, decisions and test matrix / Engineering | DONE | [PR #35](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/35), merge `5194f27551b4fad534915fbdd21e4d16febb77ff` | Planning documents merged to main on 2026-09-14; this does not accept later implementation |
| P02 | Establish updates during work and on PR events / Engineering | DONE | Contributor rules/template merged in PR #35; its merge triggered the first evidence reconciliation | Event coverage limits remain documented; ongoing maintenance is L04 |
| R01 | Pin ArduPlane/ArduCopter, BlueOS, host OS and upstream applet / Integration | BLOCKED | Need intended firmware versions and exact build capabilities | Compatibility record with immutable references, Lua/precland availability and mode support |
| R02 | Identify cameras, gimbal, feedback and video interfaces / Integration | BLOCKED | Need model/SKU/firmware and control interface | Separate fixed/gimbal capability records; verify feedback semantics and camera geometry |
| R03 | Define accuracy, range, latency and resource budgets / Product + Engineering | BLOCKED | Need operating envelope and acceptance targets | Numeric pass/fail limits; no unspecified thresholds at qualification |
| R04 | Decide acquisition, target-loss, override and touchdown policy / Product + Flight test | BLOCKED | Resolve O04 in decision log | State/transition table, authority and fallback policy for every intended mode |
| R05 | Finalise coordinate, timing, health and version contracts / Engineering | IN PROGRESS | D10 documents the implemented frame/clock handling; exposure-time mapping, R01–R04 and aircraft recovery policy remain open | Reviewed interfaces, measured timing and migration design still required; receipt-time bounds are not exposure-time synchronisation |
| REF01 | Compare Landmark with Wingxtra / Engineering | BLOCKED | Boot-data inspection complete; need the root filesystem/application, startup and active configuration, hardware/settings and reference recordings | [LMBOOT-001](LANDMARK_REFERENCE_REVIEW.md) records calibration/layout compatibility and a Wingxtra synthetic failure. Landmark's algorithm and observed output remain unexamined. Missing reference inputs do not block independent Wingxtra work; the confirmed B01 defect does gate Wingxtra acceptance. |
| F01 | Vendor a versioned Wingxtra QuadPlane applet / Engineering | DONE | Merged in PR #36; R01/R04/R05 separately gate firmware/SITL and aircraft acceptance | Applet pins upstream `9456449a442617b2af1c3132b64c3120f1694583`, preserves GPL-3.0-or-later provenance and documents installation |
| F02 | Correct acceptance order and robust applet guards / Engineering | IN PROGRESS | Independent applet review and version-matched Lua/SITL tests remain | The corrected roll/pitch/yaw return handling and guards are merged as `4819cebf823f573c738f343304556fa85ffdb88d`; all 12 Lua API-stub scenarios pass in post-merge CI run 34841164832, including missing feedback and fixed-mode independence. Firmware/SITL acceptance remains pending. |
| F03 | Add flight-controller readiness and loss supervision / Engineering | IN PROGRESS | R04–R05 remain required for policy completion | Merged applet withholds navigation updates on unavailable target/gimbal inputs; total companion failure and target-loss aircraft policy are not yet accepted |
| F04 | Preserve fixed-camera operation and introduce explicit camera modes / Engineering | DONE | Merged in PR #36; physical fixed-camera commissioning remains F05 | Automated regressions show `fixed` retains the constant BODY_FRD transform and never calls the mount API; `gimbal` selection is explicit. CI run 34841164832 passes on the merge. |
| F05 | Commission fixed camera on CM4/BlueOS/Pixhawk and simulate intended modes / Integration | PLANNED | B01 correction/regressions, F02–F04, R01–R03 | Fixed-camera portions of T01–T04 and T09–T13; measured load, latency, power and routing. T02 now includes the reproduced mixed-size planar rejection. T08 remains under M4 and T14 under M6. |
| V01 | Prepare fixed-camera flight test and recovery procedure / Flight test | PLANNED | M2, R03–R04 | Approved envelope, locations, operator authority and pass/fail criteria |
| V02 | Perform and analyse controlled fixed-camera flights / Flight test | PLANNED | V01 | Raw logs/video references, configuration hashes, measured accuracy and all failures retained |
| V03 | Qualify a named fixed-camera aircraft combination / Product + Flight test | PLANNED | V02 | Signed/attributed acceptance for that exact combination; limitations recorded |
| G01 | Implement one gimbal capability/telemetry adapter / Engineering | IN PROGRESS | Review aircraft-attitude ingestion and per-source clocks; identify the first gimbal under R02 | Real MAVLink decoding regressions cover selected autopilot identity, both attitude message formats, per-device clocks and ambiguous IDs; hardware-specific acceptance remains |
| G02 | Add frame-to-attitude time alignment / Engineering | IN PROGRESS | Review D10 and measure camera/telemetry latency; complete T07 bench cases | Frozen device time no longer renews samples; aircraft/frame/gimbal skew and age are gated. Software regressions cover repeat, reorder, startup, wrap, reboot and peer changes; exposure-time mapping remains unresolved |
| G03 | Implement dynamic target transformation and lever-arm handling / Engineering | IN PROGRESS | Independently review the full aircraft-frame composition; complete T06 bench/HIL and O06 | Tilted-aircraft/off-axis vectors pass independent geometry and decoded BODY_FRD message tests, including explicit/legacy yaw flags and quaternion signs; moving optical-centre compensation remains unresolved |
| G04 | Add landing pointing and control ownership / Engineering | IN PROGRESS | R04 policy and device/SITL tests still required | Applet defaults to external pointing, offers opt-in downward command and always requires measured pitch inside tolerance |
| G05 | Add gimbal readiness, UI diagnostics and calibration-profile checks / Engineering | IN PROGRESS | Review new aircraft/clock diagnostics and complete integrated failure injection | Invalid feedback cannot fall back to older healthy samples; stale aircraft or gimbal data inhibits output. Advancing timestamps with a frozen estimate remain an undetectable failure without additional device evidence |
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

1. Correct the reproduced B01 multi-tag rejection with regression coverage for valid mixed-size planar boards while preserving rejection of contradictory observations (T02). Verify the supported pip and Debian OpenCV paths; no correction is implemented in this documentation review. In parallel, pin the intended ArduPlane/ArduCopter builds, BlueOS/host versions and first fixed-camera model/optics (R01–R02), and agree measurable landing requirements and failure/override behaviour (R03–R04).
2. Complete F02–F03 review and version-matched fixed-camera SITL for the intended flight modes and failure cases. The local Lua harness checks mount handling with API stubs; it does not exercise all T09–T12 navigation or recovery cases.
3. Commission the fixed-camera path on the selected CM4/Pixhawk assembly (F05): calibration and physical board scale, axes/offsets, routing, latency, startup, power and thermal/load measurements. Proceed to V01–V03 controlled flight qualification only after the applicable gates pass.
4. Identify and integrate one gimbal (G01–G06), measure exposure/attitude timing and optical-centre offsets, and verify pointing ownership and failure behaviour. Preserve fixed-camera regressions and complete Q01–Q03 before claiming gimbal flight qualification. Active search/tracking remains deferred.
5. Obtain the remaining Landmark root-filesystem/application and reference-observation evidence identified in [LMBOOT-001](LANDMARK_REFERENCE_REVIEW.md#remaining-inputs). Confirm the physical board and calibrated stream rather than assuming either supplied layout was active. Package matched extension/applet versions and tested rollback under L01 when integration evidence supports the release.

There are no committed calendar delivery dates. Estimate effort after requirements and hardware access are known; record changes without erasing earlier estimates or decisions.

## How updates are maintained

- During active work, update this register, affected decisions and progress history alongside each meaningful change. The [contributor instructions](../AGENTS.md) and [PR checklist](../.github/pull_request_template.md) preserve this requirement for later sessions.
- A GitHub automation named **Update Wingxtra project progress** was created and enabled on 2026-09-14 for this repository. It responds to supported PR open/ready/close/merge events, new commits on PRs, human reviews and new PR conversation/inline comments. The PR #35 merge event produced the first live evidence reconciliation on 2026-09-14.
- After PR #35 is merged, the watcher reads current repository/PR evidence and proposes necessary tracker changes in a documentation-only PR, reusing an open progress PR where possible. It does not implement features, deploy, modify aircraft settings, send messages to other people or merge automatically. No substantive change means no update/notification; its own bookkeeping must not trigger a loop.
- Standalone pushes without a PR, CI completion by itself, edited/deleted comments and offline bench/flight work are not direct event triggers. Those facts are incorporated during active work or the next relevant review. Supply external test evidence before a hardware or flight task can be marked complete.
