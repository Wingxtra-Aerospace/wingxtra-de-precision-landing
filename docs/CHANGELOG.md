# 1.0.0-rc.2 — second review and failure-case fixes

- Post-merge packaging review: added the author email required by the [BlueOS manifest schema](https://github.com/BlueRobotics/BlueOS/blob/master/core/services/kraken/manifest/models.py), using the public contact on [Wingxtra's company page](https://wingxtra.com/company/). The previous author object failed upstream schema validation. Native container checks now inspect the built image's author metadata as well as startup and service registration. This corrects catalog metadata and does not change the landing engine.
- Fixed malformed board-corner imports returning HTTP 500, including scalar, object and overflowing integer inputs. Mixed corner winding is now rejected.
- Fixed mirrored printable tags for boards using y-down coordinates. Tests decode the actual SVG output for both axis conventions, including all ten original-board tags.
- Replaced application-read heartbeat timestamps with Linux kernel arrival timestamps. Expired queued packets and undrained telemetry backlogs cannot authorize output. UDP datagrams must contain complete MAVLink messages.
- Recheck telemetry immediately before setup edits and after slow camera shutdown/calibration solving. After any aircraft telemetry has been seen, setup requires a fresh disarmed heartbeat, including after endpoint changes.
- Made output initialization transactional. An unavailable DataBus transport cannot silently select raw UDP, and hostname resolution occurs before the output loop.
- Latch failed camera shutdowns, reject reopening until restart, clear frames on cleanup errors, and close telemetry during shutdown even if the camera driver fails.
- Expire stale preview responses; clear browser measurements and previews after a failed or stalled status request. Keep calibration controls locked while busy or setup is locked.
- Honor explicit empty/zero DataBus overrides so invalid values are rejected instead of silently ignored.
- Bumped candidate metadata and replaced the temporary-branch README URL. Added explicit Linux socket and QuadPlane integration requirements.

See [second review](SECOND_REVIEW.md) for findings, regression evidence and remaining aircraft validation.

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
