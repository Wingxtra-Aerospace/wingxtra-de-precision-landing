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
