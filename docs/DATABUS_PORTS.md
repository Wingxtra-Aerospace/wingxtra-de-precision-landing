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
When `databus_port` is missing, it fails fast with a clear error.

## Port discovery behavior

No runtime auto-discovery is performed. Endpoint resolution is explicit (CLI/ENV/config only).

## Operational guidance for Wingxtra now

- Set `mavlink_out.databus_host` and `mavlink_out.databus_port` explicitly per drone,
  or pass host/port at launch via CLI/ENV.
- Keep values under configuration management per aircraft.
- Do not rely on default assumptions across mixed fleets.
