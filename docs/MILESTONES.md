# Wingxtra Precision Landing Milestones

## Milestone A — Repo is clean, runnable, and safe

Status: ✅ in progress branch (criteria implemented)

Done when:

config.yaml is valid multi-line YAML (not one-liner).

main.py no longer contains the :contentReference[...] artifact.

python -m py_compile succeeds on all modules.

camera.yaml missing → program fails fast with a clear message (already merged by you).

## Milestone B — Offline test mode (no Pi/camera needed)

Status: ✅ in progress branch (criteria implemented)

Done when:

Add CLI support to run on prerecorded frames:

--video path.mp4 OR --images path/dir

Dry-run + debug overlay work with file input:

prints IDs, num_markers_used, x/y/z, FPS

can save snapshots

## Milestone C — DataBus integration (no serial, no FC port)

Status: ✅ in progress branch (criteria implemented)

Done when:

Implement DroneEngageDatabusInternalMavlinkOut.send_landing_target() using DroneEngage DataBus library.

Must publish TYPE_AndruavMessage_INTERNAL_MAVLINK = 6504.

Must use binary message format (sendBMSG) as per DataBus library.

Must not open /dev/serial0.

## Milestone D — DataBus port discovery + sniff/probe (no more “assumed ports”)

Status: ⬜ pending

Done when:

No hardcoded DataBus port (not 6000/60000)

Support:

CLI --databus-host --databus-port

Env overrides DATABUS_HOST DATABUS_PORT

If not provided → auto-discover:

parse DroneEngage configs if present

probe a candidate list

--databus-sniff to infer active port from UDP traffic

## Milestone E — Landing stability features (multi-size tags)

Status: ✅ in progress branch (criteria implemented)

Done when:

Adds reprojection error computation + gating

Adds EMA smoothing (configurable)

Adds stale timeout: if target unseen for N ms → stop sending LANDING_TARGET

## Milestone F — Deployable on Wingxtra drones

Status: ✅ in progress branch (criteria implemented)

Done when:

Provide systemd/wingxtra-precision-landing.service template

Provide scripts/install.sh and scripts/run.sh

README: “per-drone setup” checklist + preflight checklist

Definition of “Project Complete” = Milestones A–F all .
