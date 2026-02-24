# DroneEngage DataBus Ports – Wingxtra Policy

This document explains **how DataBus ports are handled** in the Wingxtra Precision Landing plugin
and **why no port is hardcoded**.

This exists because past implementations failed when assuming ports like `6000` or `60000`.

---

## Key Design Rule (Non-Negotiable)

**This plugin NEVER binds to a UDP port.**

- It is a **send-only publisher**
- The OS assigns an ephemeral source port automatically
- DroneEngage (`de_comm`) owns all listening sockets
- This plugin only needs the **destination host + port**

This prevents:
- port conflicts
- silent packet loss
- multiple modules fighting for the same socket

---

## Why We Do NOT Assume 6000 / 60000

Although DroneEngage documentation often mentions ports like:
- `6000`
- `60000`

In real deployments:
- the port may differ
- the port may be reassigned
- multiple DroneEngage instances may exist
- system firewalls may redirect traffic

Why We Do NOT Implement Sniffing

Sniffing (raw sockets, CAP_NET_RAW) was considered and rejected because:

requires root or special capabilities

fragile across kernels and interfaces

unnecessary for a send-only publisher

adds risk to flight-critical software

Sniffing is acceptable for manual debugging, not for production flight systems.

How Wingxtra Determines the Correct Port (Operational Guidance)

To find the active DataBus port on a drone:

Option 1 – Check DroneEngage configuration

Look for de_comm / communication config files in:

/etc/droneengage/

/opt/droneengage/

deployment .env files

systemd service files

Option 2 – Check running sockets
sudo ss -lunp | grep de_comm

or

sudo netstat -lunp | grep de_comm
Option 3 – Ask DroneEngage maintainers

Preferred for fleet deployments.

Once known:

set the port via ENV, CLI, or config.yaml

keep it consistent per deployment

Example: Recommended Production Setup
config.yaml
mavlink_out:
  mode: droneengage_databus
  databus_host: 127.0.0.1
  databus_port: 61234
systemd override
Environment=DATABUS_PORT=61234
Summary (Read This First)

❌ No hardcoded ports

❌ No sniffing

❌ No UDP bind/listen

✅ Send-only UDP

✅ Destination configured per deployment

✅ Fail fast if misconfigured

This guarantees:

zero port conflicts

predictable behavior

safe coexistence with DroneEngage

This policy is intentional and must not be “simplified” in future changes.

Wingxtra has already encountered failures caused by assuming these ports.

**Therefore: no default port is baked into code.**

---

## How the Plugin Determines the DataBus Destination

### Priority Order (highest → lowest)

1. **CLI arguments**
   ```bash
   --databus-host 127.0.0.1
   --databus-port 61234

2. Environment variables

export DATABUS_HOST=127.0.0.1
export DATABUS_PORT=61234

3. config.yaml

mavlink_out:
  mode: droneengage_databus
  databus_host: 127.0.0.1
  databus_port: 61234

If no port is provided by any of the above:

the program fails fast

a clear error is printed explaining how to set it

This is intentional.
