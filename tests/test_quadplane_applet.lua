-- Execute the real applet with firmware API stubs. This is not a SITL test.
-- Run from the repository root: lua5.3 tests/test_quadplane_applet.lua

local cases = 0

local function check(name, camera_mode, attitude, expected_updates, control)
    local values = {
        PLND_ENABLED = 1, PLND_OPTIONS = 0, PLND_XY_DIST_MAX = 0,
        WXPL_CAM_MODE = camera_mode, WXPL_MNT_CTRL = control or 0
    }
    local updates, attitude_reads, commands = 0, 0, 0
    local errors = {}
    local location = {}
    function location:copy() return self end
    function location:lat() return 1 end
    function location:lng() return 2 end
    function location:alt() return 3 end
    function location:get_distance() return 1 end

    local env = setmetatable({
        Parameter = function(key)
            return { get = function() return assert(values[key]) end }
        end,
        param = {
            add_table = function() return true end,
            add_param = function(_, _, _, key, default)
                key = "WXPL_" .. key
                if values[key] == nil then values[key] = default end
                return true
            end
        },
        uint32_t = function(value) return value end,
        millis = function() return 3000 end,
        gcs = { send_text = function(_, severity, message)
            if severity <= 3 then errors[#errors + 1] = message end
        end },
        rc = { get_aux_cached = function() return nil end },
        quadplane = { in_vtol_land_descent = function() return true end },
        vehicle = {
            get_mode = function() return 20 end,
            get_target_location = function() return location end,
            update_target_location = function()
                updates = updates + 1
                return true
            end
        },
        precland = {
            healthy = function() return true end,
            target_acquired = function() return true end,
            get_target_location = function() return location end,
            get_target_velocity = function() return nil end
        },
        ahrs = { get_location = function() return location end },
        Vector2f = function()
            return { x = function() return 0 end, y = function() return 0 end }
        end,
        logger = { write = function() end },
        mount = {
            get_attitude_euler = function(_, instance)
                assert(camera_mode == 1, "fixed mode must not read the mount")
                assert(instance == 0)
                attitude_reads = attitude_reads + 1
                return attitude()
            end,
            set_angle_target = function(_, instance, roll, pitch, yaw, earth_frame)
                assert(camera_mode == 1, "fixed mode must not command the mount")
                assert(instance == 0 and roll == 0 and pitch == -90 and yaw == 0)
                assert(earth_frame == false)
                commands = commands + 1
                -- This Lua binding has no return value.
            end
        }
    }, { __index = _G })

    local applet = assert(loadfile("applets/wingxtra_plane_precland.lua", "t", env))
    local callback, period = applet()
    assert(#errors == 0, name .. ": " .. table.concat(errors, "; "))
    assert(type(callback) == "function" and period == 50, name .. ": scheduler")
    assert(updates == expected_updates, name .. ": unexpected navigation update")
    assert(attitude_reads == camera_mode, name .. ": unexpected attitude reads")
    assert(commands == (camera_mode == 1 and control == 1 and 1 or 0),
        name .. ": unexpected mount command")
    cases = cases + 1
end

check("fixed mode is independent of mount API", 0, function() return nil end, 1, 1)
check("zero roll and downward pitch", 1, function() return 0, -90, 0 end, 1)
check("yaw does not replace pitch", 1, function() return 0, -90, 135 end, 1)
check("downward-valued yaw cannot authorise level pitch", 1,
    function() return 0, 0, -90 end, 0)
check("no measured attitude", 1, function() return nil end, 0)
check("missing pitch", 1, function() return 0, nil, -90 end, 0)
check("missing roll", 1, function() return nil, -90, 0 end, 0)
check("pitch outside tolerance", 1, function() return 0, -79, 0 end, 0)
check("pitch inside tolerance", 1, function() return 0, -81, 0 end, 1)
check("non-finite pitch", 1, function() return 0, 0 / 0, 0 end, 0)
check("command requires measured readiness", 1, function() return nil end, 0, 1)
check("command and measured downward pitch", 1, function() return 0, -90, 30 end, 1, 1)

print(string.format("%d applet scenarios passed (%s; firmware API stubs)", cases, _VERSION))
