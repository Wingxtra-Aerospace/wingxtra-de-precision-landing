# Wingxtra QuadPlane precision-landing applet

`wingxtra_plane_precland.lua` is a Wingxtra adaptation of ArduPilot's
`libraries/AP_Scripting/applets/plane_precland.lua`, pinned to upstream commit
[`9456449a442617b2af1c3132b64c3120f1694583`](https://github.com/ArduPilot/ardupilot/commit/9456449a442617b2af1c3132b64c3120f1694583).

The applet is GPL-3.0-or-later and is covered by [COPYING](COPYING). The rest of
the Wingxtra extension remains under its repository licence. Keep the applet's
header, provenance and GPL notice when redistributing it.

## Behaviour

- `WXPL_CAM_MODE=0`: fixed camera; the applet never calls the mount API.
- `WXPL_CAM_MODE=1`: gimbal camera; measured mount pitch must be inside
  `WXPL_MNT_TOL` of `WXPL_MNT_PIT` before a precision target can change
  navigation.
  The Lua mount binding returns roll, pitch and yaw directly, with `nil` when
  unavailable. Readiness uses measured pitch; yaw cannot substitute for pitch.
- `WXPL_MNT_CTRL=0` (default): another declared controller/operator positions
  the gimbal.
- `WXPL_MNT_CTRL=1`: the applet repeatedly commands the selected mount to the
  configured landing pitch while precision landing is active. Confirm control
  ownership and override/recovery behaviour before enabling this on an aircraft.
- `WXPL_ALT_CUT=0` keeps operation independent of a downward rangefinder.
  A positive value deliberately makes valid downward rangefinder data mandatory.
- Distance, location, gimbal and optional range gates are evaluated before
  `vehicle:update_target_location`.

## Installation boundary

Copy only the Lua file to the flight controller's `APM/scripts` directory and
restart the controller. Do not install both this applet and another Plane
precision-landing applet. Required firmware build features, exact parameters,
modes and recovery policy must be verified for the selected ArduPlane release.

This repository does not yet claim SITL, bench, HIL or flight acceptance for the
applet. Use the project's validation matrix and record the exact firmware,
applet hash, extension image, parameters and evidence.

## Software regression check

Run `lua5.3 tests/test_quadplane_applet.lua` from the repository root. CI runs
the same harness against the actual applet with firmware API stubs, covering
fixed-mode independence, pitch/yaw selection, missing attitude and optional
mount commands. These checks do not establish installed-firmware or SITL
acceptance.
