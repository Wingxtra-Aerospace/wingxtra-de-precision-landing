-- SPDX-License-Identifier: GPL-3.0-or-later
-- Wingxtra QuadPlane precision-landing applet
--
-- Adapted from ArduPilot plane_precland.lua at:
-- 9456449a442617b2af1c3132b64c3120f1694583
--
-- Fixed-camera mode never calls the mount API. Gimbal mode can either verify a
-- gimbal positioned by another controller or, when explicitly enabled, command
-- the selected mount down and wait for measured attitude before using the target.

---@diagnostic disable: param-type-mismatch

local MAV_SEVERITY = {
    EMERGENCY=0, ALERT=1, CRITICAL=2, ERROR=3, WARNING=4,
    NOTICE=5, INFO=6, DEBUG=7
}
local MODE_QLAND = 20
local MODE_QLOITER = 19
local AUX_PRECLOITER = 39
local RANGEFINDER_DOWN = 25
local UPDATE_MS = 50
local PARAM_TABLE_KEY = 87
local PARAM_PREFIX = "WXPL_"

local function bind_param(name)
    return Parameter(name)
end

local function bind_add_param(name, index, default_value)
    assert(param:add_param(PARAM_TABLE_KEY, index, name, default_value),
           string.format("could not add %s%s", PARAM_PREFIX, name))
    return bind_param(PARAM_PREFIX .. name)
end

assert(param:add_table(PARAM_TABLE_KEY, PARAM_PREFIX, 8),
       "could not add WXPL parameter table")

-- WXPL_ENABLE: master switch for this applet (0 disabled, 1 enabled)
local WXPL_ENABLE = bind_add_param("ENABLE", 1, 1)
-- WXPL_ALT_CUT: optional downward-rangefinder final correction cutoff; 0 disables it
local WXPL_ALT_CUT = bind_add_param("ALT_CUT", 2, 0)
-- WXPL_DIST_MAX: ignore targets farther than this horizontal distance; 0 disables it
local WXPL_DIST_MAX = bind_add_param("DIST_MAX", 3, 0)
-- WXPL_CAM_MODE: 0 fixed camera, 1 gimbal camera
local WXPL_CAM_MODE = bind_add_param("CAM_MODE", 4, 0)
-- WXPL_MNT_INST: AP_Mount instance used in gimbal mode
local WXPL_MNT_INST = bind_add_param("MNT_INST", 5, 0)
-- WXPL_MNT_CTRL: 0 external/operator points gimbal, 1 applet commands landing attitude
local WXPL_MNT_CTRL = bind_add_param("MNT_CTRL", 6, 0)
-- WXPL_MNT_PIT: commanded/required landing pitch in degrees
local WXPL_MNT_PIT = bind_add_param("MNT_PIT", 7, -90)
-- WXPL_MNT_TOL: maximum pitch error in degrees before target use is inhibited
local WXPL_MNT_TOL = bind_add_param("MNT_TOL", 8, 10)

local PLND_ENABLED = bind_param("PLND_ENABLED")
local PLND_XY_DIST_MAX = bind_param("PLND_XY_DIST_MAX")
local PLND_OPTIONS = bind_param("PLND_OPTIONS")

local precloiter_enabled = false
local have_target = false
local camera_ready_last = nil
local last_warning_ms = uint32_t(0)

local function warn_rate_limited(text)
    local now = millis()
    if now - last_warning_ms >= 2000 then
        gcs:send_text(MAV_SEVERITY.WARNING, text)
        last_warning_ms = now
    end
end

local function update_target()
    local healthy = precland:healthy()
    local acquired = healthy and precland:target_acquired()
    if acquired ~= have_target then
        have_target = acquired
        gcs:send_text(
            MAV_SEVERITY.INFO,
            acquired and "WXPL: Target acquired" or "WXPL: Target lost"
        )
    end
end

local function precision_landing_active()
    local mode = vehicle:get_mode()
    if mode == MODE_QLOITER then
        return precloiter_enabled
    end
    return quadplane:in_vtol_land_descent() or mode == MODE_QLAND
end

local function precloiter_check()
    local position = rc:get_aux_cached(AUX_PRECLOITER)
    if position == nil then
        return
    end
    local enabled = position == 2
    if enabled ~= precloiter_enabled then
        precloiter_enabled = enabled
        gcs:send_text(
            MAV_SEVERITY.INFO,
            enabled and "WXPL: PrecLoiter enabled" or "WXPL: PrecLoiter disabled"
        )
    end
end

local function camera_ready()
    if WXPL_CAM_MODE:get() < 1 then
        camera_ready_last = true
        return true
    end

    local instance = math.floor(WXPL_MNT_INST:get())
    local pitch_target = WXPL_MNT_PIT:get()
    if WXPL_MNT_CTRL:get() > 0 then
        mount:set_angle_target(instance, 0, pitch_target, 0, false)
    end

    -- The Lua binding returns roll, pitch, yaw (or nil), without a success flag.
    local roll_deg, pitch_deg = mount:get_attitude_euler(instance)
    local ready = roll_deg ~= nil and pitch_deg ~= nil
        and math.abs(pitch_deg - pitch_target) <= WXPL_MNT_TOL:get()
    if ready ~= camera_ready_last then
        camera_ready_last = ready
        gcs:send_text(
            ready and MAV_SEVERITY.INFO or MAV_SEVERITY.WARNING,
            ready and "WXPL: Gimbal in landing position"
                or "WXPL: Waiting for measured gimbal attitude"
        )
    end
    return ready
end

local function update()
    if WXPL_ENABLE:get() < 1 or PLND_ENABLED:get() < 1 then
        return
    end

    precloiter_check()
    local next_wp = vehicle:get_target_location()
    if next_wp == nil or not precision_landing_active() then
        return
    end
    if not camera_ready() then
        return
    end

    update_target()
    if not have_target then
        return
    end

    local target = precland:get_target_location()
    local vehicle_location = ahrs:get_location()
    if target == nil or vehicle_location == nil then
        warn_rate_limited("WXPL: Target or vehicle location unavailable")
        return
    end

    local range_m = -1
    local alt_cutoff = WXPL_ALT_CUT:get()
    if alt_cutoff > 0 then
        if not rangefinder:has_data_orient(RANGEFINDER_DOWN) then
            warn_rate_limited("WXPL: Downward rangefinder unavailable")
            return
        end
        range_m = rangefinder:distance_orient(RANGEFINDER_DOWN)
        if range_m < alt_cutoff then
            return
        end
    end

    local new_wp = next_wp:copy()
    new_wp:lat(target:lat())
    new_wp:lng(target:lng())
    local horizontal_distance = vehicle_location:get_distance(new_wp)
    if horizontal_distance == nil then
        warn_rate_limited("WXPL: Unable to calculate target distance")
        return
    end

    local distance_cutoff = WXPL_DIST_MAX:get()
    if distance_cutoff > 0 and horizontal_distance > distance_cutoff then
        return
    end

    -- All health, camera, range and distance gates are checked before navigation changes.
    if not vehicle:update_target_location(next_wp, new_wp) then
        warn_rate_limited("WXPL: Flight controller rejected target update")
        return
    end

    local target_velocity = precland:get_target_velocity()
    if target_velocity and (PLND_OPTIONS:get() & 1) ~= 0 then
        if not vehicle:set_velocity_match(target_velocity) then
            warn_rate_limited("WXPL: Velocity-match request rejected")
        end
    end
    if not target_velocity then
        target_velocity = Vector2f()
    end

    if PLND_XY_DIST_MAX:get() > 0
        and horizontal_distance > PLND_XY_DIST_MAX:get() then
        if not vehicle:set_land_descent_rate(0) then
            warn_rate_limited("WXPL: Descent-pause request rejected")
        end
    end

    logger.write(
        "WPLD", "Lat,Lon,Alt,HDist,RFND,VN,VE",
        "LLfffff", "DUmmmmm", "GG-----",
        new_wp:lat(), new_wp:lng(), new_wp:alt(),
        horizontal_distance, range_m,
        target_velocity:x(), target_velocity:y()
    )
end

gcs:send_text(MAV_SEVERITY.INFO, "WXPL: Loaded")

local function protected_wrapper()
    local success, err = pcall(update)
    if not success then
        gcs:send_text(MAV_SEVERITY.ERROR, "WXPL internal error: " .. tostring(err))
        return protected_wrapper, 1000
    end
    return protected_wrapper, UPDATE_MS
end

return protected_wrapper()
