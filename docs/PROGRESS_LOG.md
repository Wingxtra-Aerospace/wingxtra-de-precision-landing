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
