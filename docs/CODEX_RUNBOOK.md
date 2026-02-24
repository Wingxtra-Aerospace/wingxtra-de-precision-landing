# CODEX RUNBOOK

This file captures the Codex prompts used in this project so Wingxtra can replay iterations.

## Prompt 1 (context/non-negotiables)

"""
get to understand the project. it is based on

for the purpose of this project these are the Context / Non-negotiables:

Single Pi / Single FC link: This project MUST NOT open /dev/serial0 or any physical MAVLink port. DroneEngage owns the FC connection. This module outputs INTERNAL MAVLink to DroneEngage, which then forwards to the flight controller. (Repo README already states this requirement.)

AprilTag multi-tag target: Use OpenCV’s aruco module with AprilTag dictionary DICT_APRILTAG_36h11 (matches landing-target.json which uses tag36h11).

No rangefinder version: We rely on PnP pose (x,y,z) from camera, so LANDING_TARGET.position_valid=1 and x,y,z must be populated in meters. (Already implemented in main.py.)

Per-drone calibration is mandatory: camera.yaml is required at runtime but must never be committed. Repo already ignores it in .gitignore, but code must fail fast if it’s missing.
"""

## Prompt 2 (runtime checks + dry run + debug overlay)

"""
Goal: On a Raspberry Pi, the program starts, detects tags, but does not attempt to talk to FC yet (because DataBus adapter is still stubbed), and it fails fast if calibration is missing.

Tasks

Add runtime checks in main.py:

If camera.yaml missing → raise a clear error telling Wingxtra to run tools/calibrate_camera.py.

If calibration resolution doesn’t match runtime resolution (config.yaml camera width/height) → raise clear error (recalibrate or match settings).

Add --dry-run mode:

Detect tags + estimate pose + print pose and tag IDs used

Do not send MAVLink anywhere

Add --debug-overlay option:

Draw detected tag borders

Print used_ids, num_markers_used, estimated x/y/z, FPS on screen

Save optional debug_frames/ snapshots

Definition of done

Running python -m src.wingxtra_pl.main --dry-run --debug-overlay works on Pi camera, shows stable detections and pose output.
"""

## Prompt 3 (formatting and hygiene)

"""
Reformat README.md into valid multi-line markdown (headings, code fences properly closed).

Reformat config.yaml into valid multi-line YAML with proper indentation.

Reformat python files (black style or similar).

Remove the stray artifact :contentReference[oaicite:...] that appears inside main.py (that will break execution).
"""

## Prompt 4 (DataBus implementation iteration)

"""
Goal: Finish wingxtra-de-precision-landing so it runs on the same Raspberry Pi as DroneEngage ... then publishes a MAVLink2 LANDING_TARGET message to DroneEngage via DataBus as INTERNAL MAVLINK.

Hard rule: This project must NOT open the FC serial port (/dev/serial0). DroneEngage owns the physical MAVLink connection.
"""

## Prompt 5 (DataBus sendBMSG specifics)

"""
Vendor (or add as dependency) the DroneEngage DataBus python client from droneengage_databus/python or re-implement only what’s needed (CModule + UDP client + sendBMSG) to keep it minimal.

Initialize the DataBus client using your config:

databus_host: 127.0.0.1

databus_port: 60000

Publish the MAVLink2 packet bytes using:

andruav_message_id = TYPE_AndruavMessage_INTERNAL_MAVLINK (6504)

binary message (DataBus sendBMSG) as shown in the Node example.
"""

## Prompt 6 (docs + hygiene scaffolding)

"""
Task: Create documentation scaffolding and fix repo hygiene.
Requirements:

Create docs/MILESTONES.md with milestones A–F exactly as described.

Create docs/CODEX_RUNBOOK.md and put all Codex prompts (including this one) in it so Wingxtra can re-run them later.

Create docs/WINGXTRA_NOTES.md (operations note) containing: per-drone camera calibration policy, how to generate camera.yaml, what triggers recalibration, preflight checklist, safety warnings.

Create docs/DATABUS_PORTS.md documenting port discovery/sniff/probe and how Wingxtra sets host/port via CLI/env/config.

Reformat config.yaml into valid multi-line YAML (it is currently one-line and fragile).

Remove the stray :contentReference[...] artifact from src/wingxtra_pl/main.py and run python -m py_compile locally to ensure code parses.
Deliverable: One PR with docs + hygiene fixes only (no new functionality yet).
"""
