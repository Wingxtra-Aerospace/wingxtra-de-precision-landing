# Second code review — 1.0.0-rc.2

Reviewed for Wingxtra Aerospace Ltd. on 2026-09-14. Starting point: merged main commit `9d75ed5` (PR #32, implementation commit `67a8af8`). This review found additional defects; rc.1 should be replaced by the tested rc.2 candidate before aircraft commissioning.

| Priority | Confirmed issue | Correction and evidence |
|---|---|---|
| High | Heartbeats sitting in the UDP receive queue were timestamped when read and could appear fresh after a processing stall. An armed heartbeat could also remain behind the 64-packet polling limit. | Kernel receive timestamps, expired-packet rejection and backlog gating. Tests reproduce delayed reads and a pending armed heartbeat behind a telemetry backlog. |
| High | Setup checked cached arming state without reading queued telemetry. A stale disarmed state permitted edits; arming during calibration solving or camera shutdown could go unnoticed before saving. | Poll immediately before changes, require fresh disarmed telemetry after any heartbeat, and recheck after slow work. Tests cover queued arming, stale disarming, solve/save and shutdown/save. |
| High | DataBus initialization could fail after the UDP listener had opened, leaving publish available and selecting raw UDP through a truthiness fallback. | All-or-nothing output initialization, explicit transport selection, early DNS resolution, socket cleanup and a regression that injects DataBus failure. |
| Medium | Camera close failures could leave a stopped driver object reusable and prevent telemetry sockets from closing. Cleanup exceptions could kill acquisition without a useful restart diagnosis. | A latched restart requirement, frame/preview clearing and guaranteed telemetry cleanup on shutdown. Tests inject both close timeout and driver-release failure. |
| Medium | Board SVG export always reflected the board Y axis, mirroring AprilTag bits for valid y-down layouts. Mixed winding was accepted even though all tags must show the same physical face. | Choose the visible face from corner winding; reject mixed winding. Regression tests rasterize the exported SVG and decode both axis conventions, including every original-board tag. |
| Medium | Malformed `object_points` values raised uncaught TypeError/OverflowError and returned HTTP 500. | Validate numeric 4x3 lists before conversion; reject huge coordinates. API tests verify HTTP 409 and unchanged saved board. This also addresses the automated PR #32 review comment. |
| Medium | Browser disconnects could leave last-good coordinates visible, and a late preview response could reveal an old image again. Status fetches had no deadline. | Clear measurements, invalidate cached status, hide stale images, add status timeouts/watchdog, expire preview responses and retain calibration button locks. Browser tests interrupt and restore status traffic. |
| Low | Explicit zero/empty DataBus overrides were ignored by the CLI truthiness check. Package metadata still linked to the temporary implementation branch. | Check whether an override was supplied, retain strict endpoint validation, update metadata and move the README URL to main. |

The new failure-case tests were run against the original code before fixes. Several malformed-input cases already rejected correctly; the newly exposed failure cases failed as expected. The small original-board SVG tags required adequate raster resolution for a meaningful print test; the corrected test decodes all ten tags without changing board dimensions or IDs.

## Verification

The repository suite now contains 70 Python tests. It exercises real OpenCV detections, actual MAVLink packet decoding and local UDP sockets as well as isolated failure injection, including explicit invalid CLI/environment overrides. A timing regression also injects an armed heartbeat during a slow receive poll: timestamp conversion advances its monotonic reference for every packet so the newer state is never mistaken for an older packet. The browser suite additionally checks loss/recovery of status traffic and clears old coordinates/previews. CI runs the same Python suite in the native ARM64 and AMD64 Debian/OpenCV runtimes, starts the actual packaged service with its container permissions, checks health/registration, and exports each image.

Install only the exact commit with a successful complete workflow; the pull request and Actions run provide the final build evidence. Synthetic camera/calibration fixtures remain test-only and output-inhibited. No real calibration or flight result is included.

## Remaining validation boundaries

- No physical camera, BlueOS companion, flight controller, SITL mission or aircraft flight was available during this code review. Container startup is not evidence of a completed landing.
- Verify the current target firmware and parameters, camera axes/lever arm, physical print scale, latency, update rate and measured landing envelope. The companion still cannot prove exposure freshness when a camera repeatedly re-encodes frozen imagery.
- Single-tag planar pose can be ambiguous or noisy, particularly when inferring an origin far outside the visible tag. Validate it physically; configure multiple-tag minimums when the required visibility envelope permits.
- QuadPlane requires its version-matched controller-side integration, as described by [ArduPilot's precision-landing documentation](https://ardupilot.org/dev/docs/mavlink-precision-landing.html) and [official Plane applet instructions](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AP_Scripting/applets/plane_precland.md). Correct sensor messages alone do not enable landing corrections.
- BODY_FRD/positive-distance handling and the additional sensor yaw/orientation rotations were checked against ArduPilot's current [MAVLink backend](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AC_PrecLand/AC_PrecLand_MAVLink.cpp) and [precision-landing frontend](https://github.com/ArduPilot/ardupilot/blob/master/libraries/AC_PrecLand/AC_PrecLand.cpp). The installed firmware must be checked separately; current upstream source is not a substitute for its actual build.
- Live DroneEngage forwarding and GHCR package visibility remain installation-specific. BlueOS raw UDP routing is the default integration path.

The result is a more thoroughly checked release candidate, with the additional defects corrected. It is not a declaration that every possible defect has been eliminated or that the system is flight qualified.
