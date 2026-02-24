# Wingxtra Precision Landing – Project Milestones

## Milestone A – Safety & Local Validation (DONE)
Goal: Code runs safely without hardware side effects.

Done when:
- Program fails fast if camera.yaml is missing.
- Program fails fast if calibration resolution mismatches config.
- --dry-run mode works (no MAVLink output).
- --debug-overlay shows detected tag IDs, pose, FPS.
- No FC serial port is ever opened.

---

## Milestone B – Offline / Hardware-Free Testing
Goal: Codex can validate logic without Raspberry Pi or camera.

Done when:
- Program supports:
  --video <file>
  --images <dir>
- AprilTag detection + pose estimation work on prerecorded frames.
- Debug overlays can be saved to disk.
- No picamera2 import required in offline mode.

---

## Milestone C – DroneEngage DataBus INTERNAL MAVLink Output
Goal: Send LANDING_TARGET via DroneEngage without touching serial.

Done when:
- DroneEngage DataBus client is integrated.
- Message type TYPE_AndruavMessage_INTERNAL_MAVLINK (6504) is used.
- Payload is binary MAVLink2 packet.
- Sender is UDP send-only (no bind, no listen).
- Destination host/port are configurable (CLI/env/config).
- No assumption of 6000/60000 anywhere in code.

---

## Milestone D – Stability for Multi-Size Tags
Goal: Landing remains stable as tag visibility changes.

Done when:
- Reprojection error is computed and gated.
- EMA smoothing is applied to x/y/z.
- Stale timeout stops LANDING_TARGET if target is lost.
- Logs include: used_ids, num_markers_used, reprojection error.

---

## Milestone E – Deployment & Operations
Goal: Wingxtra can deploy safely on every drone.

Done when:
- systemd service template exists.
- install/run scripts exist.
- README includes per-drone setup checklist.
- WINGXTRA_NOTES.md exists with calibration policy.

---

## Project Complete
The project is complete when Milestones A–E are all satisfied.
Hardware flight testing is explicitly out of scope for completion.
