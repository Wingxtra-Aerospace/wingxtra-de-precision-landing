# DataBus Host/Port Discovery and Overrides

## Priority order for host/port configuration

For reliable deployments, use this precedence:

1. CLI flags: `--databus-host`, `--databus-port`
2. Environment variables: `DATABUS_HOST`, `DATABUS_PORT`
3. `config.yaml` values:
   - `mavlink_out.databus_host`
   - `mavlink_out.databus_port`

## Current baseline behavior

Current code implements CLI/ENV/config precedence and fails fast if no destination port is provided.

## Port discovery/sniff/probe plan

To avoid assumed ports in the future implementation:

1. Parse DroneEngage config files (if present on target system) and extract active DataBus endpoint.
2. Probe a candidate port set with a lightweight handshake.
3. Add `--databus-sniff` mode to watch UDP traffic and infer active DataBus endpoint.
4. Record resolved endpoint in logs before starting landing loop.

## Operational guidance for Wingxtra now

- Set `mavlink_out.databus_host` and `mavlink_out.databus_port` explicitly per drone,
  or pass host/port at launch via CLI/ENV.
- Keep values under configuration management per aircraft.
- Do not rely on default assumptions across mixed fleets.
