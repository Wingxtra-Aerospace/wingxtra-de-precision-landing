# DataBus Host/Port Discovery and Overrides

## Priority order for host/port configuration

For reliable deployments, use this precedence:

1. CLI flags: `--databus-host`, `--databus-port`
2. Environment variables: `DATABUS_HOST`, `DATABUS_PORT`
3. `config.yaml` values:
   - `mavlink_out.databus_host`
   - `mavlink_out.databus_port`

## Current baseline behavior

Current code implements CLI/ENV/config precedence and fails fast if no destination host/port is resolved.
When `databus_port` is missing, it attempts config-file discovery from common DroneEngage locations. If unresolved, it fails fast with a clear error.

## Port discovery behavior

To avoid assumed ports, the runtime does best-effort discovery by parsing DroneEngage config files (if present on target system) and extracting explicit `databus_host` / `databus_port` values.

## Operational guidance for Wingxtra now

- Set `mavlink_out.databus_host` and `mavlink_out.databus_port` explicitly per drone,
  or pass host/port at launch via CLI/ENV.
- Keep values under configuration management per aircraft.
- Do not rely on default assumptions across mixed fleets.
