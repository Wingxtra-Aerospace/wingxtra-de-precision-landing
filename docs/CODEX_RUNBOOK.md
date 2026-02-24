# Codex Runbook – Wingxtra Precision Landing

## Core Rule
This project MUST NOT open /dev/serial0.
DroneEngage owns the FC connection.
This project publishes INTERNAL MAVLink only.

---

## Prompt 1 – Repo Hygiene
- Reformat config.yaml into valid multi-line YAML.
- Remove any stray tokens (e.g. contentReference artifacts).
- Ensure python -m py_compile passes.
- Add docs/MILESTONES.md, docs/WINGXTRA_NOTES.md, this file.

---

## Prompt 2 – Offline Input Mode
Implement:
- --video <file>
- --images <dir>
- Lazy import picamera2 (only when camera mode used).
- --debug-overlay + snapshot saving.
Definition of done:
- Offline run shows pose + detected IDs.

---

## Prompt 3 – DataBus INTERNAL MAVLink Output
Implement DroneEngage DataBus publishing:
- Use TYPE_AndruavMessage_INTERNAL_MAVLINK = 6504.
- Binary payload (MAVLink2 bytes).
- Send-only UDP (no bind).
- Configurable destination:
  CLI > ENV > config.yaml.
- No assumed ports.
Definition of done:
- Fake receiver confirms JSON header + binary payload.

---

## Prompt 4 – Stability Improvements
Implement:
- Reprojection error gating.
- EMA smoothing on pose.
- Stale timeout to stop sending when target lost.
Definition of done:
- Pose does not jump when tags flicker.

---

## Prompt 5 – Deployment
Implement:
- systemd service template.
- install.sh / run.sh.
- README deployment checklist.
