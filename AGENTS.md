# Working on Wingxtra precision landing

Read `docs/PROJECT_STATUS.md` and `docs/DECISION_LOG.md` before substantive work. Use `docs/DEVELOPMENT_PLAN.md` for scope/dependencies and `docs/VALIDATION_MATRIX.md` for acceptance. `docs/MILESTONES.md` and `docs/CODEX_RUNBOOK.md` are historical prototype records, not current requirements.

The user's latest explicit instruction governs scope. On 2026-09-14 the user authorised planning and ongoing tracking, while deferring implementation of new gimbal support and the Wingxtra QuadPlane applet. A later implementation instruction can supersede that hold; record it rather than repeatedly requesting permission already given. Do not infer implementation or deployment authorisation from this roadmap.

For every meaningful code, test, configuration, documentation, hardware-evidence or requirement change:

1. Identify affected work/test IDs; add stable IDs for genuinely new work.
2. Update task status, dependencies, next action and evidence in `docs/PROJECT_STATUS.md` as part of the same change.
3. Record changed decisions in `docs/DECISION_LOG.md`; retain superseded decisions and reasons.
4. Append a concise dated entry to `docs/PROGRESS_LOG.md` with validation and remaining limits.
5. Reopen tasks when changed code, firmware, optics, timing or operating requirements invalidate their acceptance.
6. Keep PRs in review until the relevant merge/acceptance evidence exists. Distinguish implementation, CI, SITL, bench and flight qualification. Never infer a flight result from unit tests or a successful reference system.

Documentation-only corrections need proportionate checks (content, links and diff); do not add redundant implementation tests. Preserve the existing runtime/flight behaviour during planning-only work.

Background progress reconciliation may update planning documents through a docs-only PR. It must not change flight code, install software, alter aircraft parameters, merge automatically or contact other people. Ignore its own bookkeeping events when nothing substantive changed. Record the limits of event coverage; external bench/flight work requires supplied evidence.

When a future upstream applet is added, preserve its version/provenance and licence. Do not relabel third-party code as MIT or place proprietary reference-system contents in this repository.
