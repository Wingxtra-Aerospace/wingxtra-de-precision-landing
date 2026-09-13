# 1.0.0-rc.1 — corrected engine and BlueOS packaging

- Replaced the broken publisher's duplicate `CModule` definition and missing imports with an isolated, tested DataBus sender matching upstream framing.
- Replaced BODY_NED/zero-distance position messages with MAVLink 2 BODY_FRD, positive distance, valid quaternion, vision-fiducial type and persistent packet sequence.
- Corrected the default downward-camera axes. Camera offsets are applied once in the autopilot.
- Preserved true multi-tag/common-origin estimation and added robust fitting, whole-tag outlier rejection, cheirality, tag pixel size and reprojection checks.
- Replaced unconditional camera hardware imports with live-source adapters. No prerecorded file can accidentally become the selected flight input.
- Replaced last-seen/EMA behavior with explicit frame freshness, consecutive acquisition, motion consistency and loss reset. Rejected detections do not refresh a track.
- Added bidirectional router UDP integration and autopilot heartbeat supervision. No serial, GCS heartbeat, parameter, mode or arm command is emitted.
- Added validated configuration, atomic persistence, bounded diagnostic logs, controlled startup modes and a process-wide dry-run inhibit.
- Added a browser calibration workflow with diversity, numerical RMS and intrinsic checks, camera binding, export and matching import.
- Added a BlueOS interface, relative-path assets/API, service registration, container permissions, native AMD64/ARM64 CI and image archive/registry packaging.
- Replaced obsolete install scripts and calibration helper; documented migration and aircraft commissioning. The former native YAML camera file must be recalibrated into the new schema.

This is a release candidate, not a claim of flight qualification or a published Bazaar listing.
