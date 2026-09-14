# Progress history

Append dated entries; retain earlier results and decisions. Current task states live only in [PROJECT_STATUS.md](PROJECT_STATUS.md).

## 2026-09-14 — P01/P02: establish the programme baseline

- User requested the full fixed-camera/gimbal/QuadPlane plan and continuing progress updates. Implementation of the new functionality remains on hold pending a later instruction.
- Verified main `e07fd2fefbc450313972bae3f133cf315afc0870` includes merged PR #34. Its tree is identical to `9402aab7f5e3448fe99bcb867a7588412521bb46`; [workflow 34795056753](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34795056753) reports success for that implementation. A separate successful workflow on the merge commit itself is not claimed.
- Recorded completed software deliverables separately from unperformed hardware, SITL and aircraft validation. Preserved the earlier milestone/runbook files as historical references.
- Added task IDs, milestone dependencies, acceptance criteria, unresolved inputs, a validation matrix, decision history, contributor instructions and a PR update checklist.
- Recorded the selected CM4/Pixhawk hardware, the pending Landmark reference and the reviewed gimbal/QuadPlane limitations. No camera, firmware, numeric operating envelope or failure policy was invented.
- Published the plan as [PR #35](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/35), initially at `88cb5114ec89ba7e8ebc3147fc68ba7a5ae5bee8`. The remote Git tree exactly matches the locally checked tree. P01 remains in review until merge.

## 2026-09-14 — P02: establish PR event reconciliation

- Created and enabled **Update Wingxtra project progress** for this repository. Supported PR lifecycle, commit, human-review and new-comment events trigger evidence reconciliation after the initial plan is merged.
- The watcher may propose documentation-only updates through a progress PR. It must not implement deferred features, alter aircraft configuration, deploy, contact other people or merge automatically. It skips unchanged facts and its own bookkeeping loops.
- Documented coverage limits: direct pushes without PRs, standalone CI completion, edited/deleted comments and offline tests do not directly trigger it. No live event execution is claimed yet. Contributor instructions cover updates during our active work.
- Checked Markdown links/anchors, task/test ID uniqueness, code-fence balance and whitespace. The change contains only planning/contributor documents and README/archive pointers; runtime code, applets, tests, dependency files, packaging and workflows are unchanged.
- Next: merge the planning PR, verify the first relevant reconciliation, then resolve the recorded hardware/firmware and operating-policy inputs. Feature implementation remains deferred.

## 2026-09-14 — P01/P02/F01–F04/G01–G05: authorise and start implementation

- User explicitly authorised selectable fixed/gimbal camera support and a Wingxtra QuadPlane applet, superseding the planning-only implementation hold (D09).
- PR #35 merged as `5194f27551b4fad534915fbdd21e4d16febb77ff`; the planning baseline is now on main. Its head `6f7a002ea72880a609774b31193d333435c8f430` passed [workflow 34821277783](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34821277783). This is software evidence, not SITL, bench or flight evidence.
- The first live merge reconciliation was observed. P01 and P02 meet their scoped planning/tracking acceptance; ongoing evidence maintenance remains L04.
- Started a reviewable implementation with editable camera connection presets, explicit fixed/gimbal modes, fail-closed gimbal attitude transformation, bounded receive-time matching, diagnostics and per-stream calibration identity.
- Added a Wingxtra applet derived from upstream `plane_precland.lua` at `9456449a442617b2af1c3132b64c3120f1694583`, retaining GPL provenance. The applet keeps fixed mode independent of mount APIs and supports measured, optional opt-in gimbal pointing.
- Corrected F05 so fixed-camera milestone M2 no longer depends on gimbal test T08 or release test T14, resolving the review finding on PR #35.
- Remaining: code review/CI, version-matched Lua/SITL, actual camera/gimbal identity, latency and lever-arm measurements, CM4/Pixhawk bench tests, approved recovery policy and controlled flight evidence.

## 2026-09-14 — G03: remove unused test variable

- In [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36), manually removed only the unused `half = math.sqrt(0.5)` assignment from `test_earth_frame_status_uses_delta_yaw_to_recover_vehicle_frame`; retained the assignment used by the downward-camera test. Change starts from `34516b866b4ea80c5733682efc5d7b17ab9e3f48`.
- Local validation: `ruff check --select F841 src tests` passed; `python -m pytest -q tests/test_gimbal_modes.py::test_earth_frame_status_uses_delta_yaw_to_recover_vehicle_frame` reported **1 passed**. `ruff check src tests` still reports the separate unused NumPy import (F401) in the same file.
- G03 remains IN REVIEW. This fixes one lint blocker without changing test assertions or runtime behaviour; full CI, applet review, SITL, bench and flight acceptance remain outstanding.

## 2026-09-14 — F02/G03/G04: clear lint and applet validation blockers

- Removed the unused `import numpy as np` from `tests/test_gimbal_modes.py` in [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36), starting from `e8b19575bcf404a59765b447f78ad2d0dc369ad2`. The earlier `half` fix is retained.
- Applied the existing Ruff and Prettier formatters to the six files rejected by formatting checks, without changing their behaviour.
- Corrected `mount:get_attitude_euler` unpacking using the [pinned upstream Lua API declaration](https://github.com/ArduPilot/ardupilot/blob/9456449a442617b2af1c3132b64c3120f1694583/libraries/AP_Scripting/docs/docs.lua): it returns roll, pitch and yaw without a success flag. The prior code could mistake yaw for pitch. Added an executable Lua API-stub harness and a CI step for it.
- Local validation: `ruff check src tests`, `ruff format --check src tests`, `node --check src/wingxtra_pl/static/app.js` and `npm run format:check` passed. `python -m pytest -q` reported **78 passed** with two dependency deprecation warnings. The existing browser smoke test passed. `luatex --luaonly tests/test_quadplane_applet.lua` ran Lua 5.3 and reported **12 scenarios passed**; the same harness failed against parent `e8b19575bcf404a59765b447f78ad2d0dc369ad2` on the downward-pitch case, confirming it detects the return-order defect.
- F02/G03/G04 remain IN REVIEW. Full CI/container results and independent applet review remain pending; Lua API stubs do not establish firmware/SITL, bench or flight acceptance.

## 2026-09-14 — F02/G01–G05/T06–T07: passing CI with outstanding gimbal defects

- Reconciled [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36) at `fa363e5680e577784194b3f023f114eecf16e055` against main `5194f27551b4fad534915fbdd21e4d16febb77ff`. The implementation is open/in review, not merged or accepted. Its earlier tracker changes already record the user-authorised scope (D09), PR #35's merge and the fixed-camera F05/M2 dependency correction; those facts are retained consistently here.
- The unused `half` fix (`e8b19575bcf404a59765b447f78ad2d0dc369ad2`), NumPy-import/format fixes and corrected Lua attitude-return handling (`fa363e5680e577784194b3f023f114eecf16e055`) are present. [CI run 34827077062](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34827077062) reports success, last updated 09:20:17 UTC: 78 Python tests, 12 Lua API-stub scenarios, lint/format, browser checks and native AMD64/ARM64 container validation. Exact jobs and artifact IDs are recorded in [earlier review evidence](PROJECT_STATUS.md#earlier-implementation-review--pr-36). The manifest/push stages are intentionally skipped for PRs.
- Independently verified the automated [frame-conversion finding](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36#discussion_r4003725723) and [device-time finding](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36#discussion_r4003725728) against this current tree. A read-only synthetic 10° rolled-aircraft case returns a vertical BODY_FRD target instead of the required lateral component; repeated device time with fresh receive timestamps is still accepted. The diagnostic inputs/results are recorded in PROJECT_STATUS; they are software observations, not physical measurements or chosen acceptance thresholds.
- G01–G03/G05 remain IN REVIEW with T06/T07 acceptance blocked. Clarified those matrix cases to include full aircraft-attitude composition and nonadvancing device time, reordered data and reboot/wrap policy. No gimbal task had been accepted, so no DONE task is reopened; passing CI remains valid only for the cases it exercised.
- D09 supersedes the earlier planning hold, as already proposed in PR #36; no aircraft policy, model, firmware or operating limit is newly selected. No human review/approval, SITL, bench, flight or supplied Landmark evidence was available.
- This documentation-only reconciliation records newly verified defects and completed CI evidence that PR #36's tracker did not yet contain. Next: fix the two gimbal defects with targeted regressions, retain fixed-camera coverage, then perform the remaining firmware/integration acceptance. No runtime, tests, workflows, applets or aircraft settings were modified by this reconciliation.

## 2026-09-14 — G01–G03/G05/T06–T07: correct aircraft geometry and stale device clocks

- User authorised the two remaining gimbal fixes. [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36), commit [`176c9e0c3b761a158b88058049c0176d6bb68fe1`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/176c9e0c3b761a158b88058049c0176d6bb68fe1), adds the correction starting from `fa363e5680e577784194b3f023f114eecf16e055`: selected-autopilot ATTITUDE/ATTITUDE_QUATERNION ingestion and full horizon/heading-to-BODY_FRD composition. Kept fixed mode independent and retained the configured body-down envelope.
- Added per-source clock progression, startup priming, duplicate/reorder rejection, bounded uint32 wrap and no automatic rollback/reboot rebasing. Aircraft/gimbal/frame age and pair skew are gated; invalid feedback clears healthy history and ambiguous device selection is rejected. D10 records these implementation choices without claiming physical clock synchronisation or choosing an aircraft loss policy.
- Local validation: **126 Python tests pass**, including **56 camera/gimbal tests**, with two dependency deprecation warnings; Ruff lint and formatting pass for all 32 Python files. Four new wire/service regression cases executed against the earlier source fail on the original incorrect-vector and stale-acceptance assertions; all pass on the correction. These are automated software tests, not SITL or hardware evidence.
- Preserved the earlier PR #37 review findings and CI evidence as historical records. Updated work states/next actions and T06/T07 software evidence; G01–G03/G05 remain IN REVIEW. Bench/HIL, exact camera/gimbal/firmware, exposure timing, lever arms, aircraft recovery policy and flight qualification remain open.
- [CI run 34830596708](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34830596708), attempt 1, completed successfully at the recorded head; last updated 2026-09-14 10:00:33 UTC. The Python job and both native container test runs each report **126 passed**. All **12 Lua API-stub scenarios**, lint/format, browser and container startup/health checks pass. Exact job IDs, artifact IDs and archive digests are recorded in [current correction evidence](PROJECT_STATUS.md#merged-cameragimbal-implementation). Registry/manifest publication is intentionally skipped for PRs.
- At that snapshot the implementation remained open and unmerged, with no human review submission or supplied SITL, hardware, flight or Landmark evidence. The later merge is recorded in the following entry.


## 2026-09-14 — F01–F04/G01–G05: merge selectable camera modes and applet

- [PR #36](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/pull/36) merged on 2026-09-14 as [`4819cebf823f573c738f343304556fa85ffdb88d`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/4819cebf823f573c738f343304556fa85ffdb88d). Its tree `42cc5f3d12889773577922c3776c0217cd04cfc6` exactly matches tested source head `176c9e0c3b761a158b88058049c0176d6bb68fe1`. The PR records one automated COMMENTED review and no human review submission; the human merge is recorded separately from code-review evidence.
- [Post-merge workflow 34841164832](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/actions/runs/34841164832) completed successfully at 12:05:53 UTC. Python job `103966236658`, AMD64 job `103966538527`, ARM64 job `103966538606` and manifest job `103967428823` pass. The Python and both native container runs report **126 tests passed**; **12 Lua API-stub scenarios**, browser, formatting and container startup/health checks pass.
- The workflow published immutable AMD64 digest `sha256:b15e1f19d3a2233e6ad77cc2e433c035863e97d5231551d8009c2d3d558e3043`, ARM64 digest `sha256:c3c01bc9c9f39b547f162af30f85ee81cd36f45f53870e647777684c4843792e` and combined manifest `sha256:f1c4de51d21dc098b99d9b00298835ee90d7f969fd2d90bffdeef8c56449a90d` under commit-qualified GHCR tags. Artifacts: Python `10345699451`, AMD64 `10345879304`, ARM64 `10345993646`.
- F01 and F04 now meet their scoped merged-software acceptance. F02–F03 and G01–G05 remain IN PROGRESS because version-matched SITL, measured timing/geometry, selected hardware, control/loss policy and integrated acceptance are outstanding. No CM4 installation, physical-camera/gimbal test, aircraft-setting change, flight qualification or Landmark comparison is inferred.
- PR #37 was reconciled onto current main as a five-document tracking update. Next: complete R01–R04 inputs, version-matched SITL and the CM4/Pixhawk/camera/gimbal bench matrix before controlled flight work.

## Entry template

Copy for the next meaningful change:

```text
Date / task IDs / short description:
Previous state -> new state:
What changed and why:
Commit / PR / artifact references:
Validation performed and exact result:
Limitations / evidence invalidated:
Decisions resolved or superseded:
Blockers and next action:
```

Do not mark a task done merely because its PR opened, tests were proposed or a different system landed successfully. Automated reconciliation should avoid entries for events that do not change a tracked fact.
