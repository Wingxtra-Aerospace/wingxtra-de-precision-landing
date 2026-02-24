# DataBus Host/Port Discovery and Overrides

## Priority order for host/port configuration

For reliable deployments, use this precedence:

1. CLI flags: `--databus-host`, `--databus-port`
2. Environment variables: `DATABUS_HOST`, `DATABUS_PORT`
3. `config.yaml` values:
   - `mavlink_out.databus_host`
   - `mavlink_out.databus_port`

Optional helper:

- `--databus-sniff` to explicitly probe candidate ports from:
  - `--databus-sniff-ports`
  - `mavlink_out.databus_candidate_ports`
  - `DATABUS_CANDIDATE_PORTS`

## Current baseline behavior

Current code implements CLI/ENV/config precedence and fails fast if no destination host/port is resolved.
When `databus_port` is missing, it now attempts automatic discovery in this order:

1. Parse common DroneEngage config locations for DataBus host/port.
2. Probe candidate ports (`--databus-sniff-ports`, `mavlink_out.databus_candidate_ports`, `DATABUS_CANDIDATE_PORTS`).
3. If still unresolved, fail fast with a clear error.

## Port discovery/sniff/probe behavior

To avoid assumed ports, the runtime does best-effort discovery:

1. Parse DroneEngage config files (if present on target system) and extract active DataBus endpoint.
2. Probe a candidate port set with a lightweight UDP probe payload.
3. Keep `--databus-sniff` as an explicit alias for probing candidates.

## Operational guidance for Wingxtra now

- Set `mavlink_out.databus_host` and `mavlink_out.databus_port` explicitly per drone,
  or pass host/port at launch via CLI/ENV.
- Keep values under configuration management per aircraft.
- Do not rely on default assumptions across mixed fleets.
