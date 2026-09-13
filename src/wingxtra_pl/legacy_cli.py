"""Endpoint precedence retained for migrating native DroneEngage installations."""

import os


def _parse_port(value, source: str) -> int | None:
    if value is None:
        return None
    try:
        port = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid DataBus port from {source}: {value!r}") from exc
    if port < 1 or port > 65535:
        raise ValueError(f"Invalid DataBus port from {source}: {value!r} (expected 1..65535)")
    return port


def _parse_host(value, source: str) -> str | None:
    if value is None:
        return None
    host = str(value).strip()
    if not host:
        raise ValueError(f"Invalid DataBus host from {source}: {value!r}")
    return host


def resolve_databus_endpoint(args, cfg) -> tuple[str, int]:
    cfg_host = cfg["mavlink_out"].get("databus_host")
    cfg_port = cfg["mavlink_out"].get("databus_port")

    host = _parse_host(args.databus_host, "--databus-host")
    if not host:
        host = _parse_host(os.getenv("DATABUS_HOST"), "environment variable DATABUS_HOST")
    if not host:
        host = _parse_host(cfg_host, "config.yaml:mavlink_out.databus_host")

    cli_port = _parse_port(args.databus_port, "--databus-port")
    if cli_port is not None:
        port = cli_port
    else:
        env_port_raw = os.getenv("DATABUS_PORT")
        env_port = _parse_port(env_port_raw, "environment variable DATABUS_PORT")
        if env_port is not None:
            port = env_port
        else:
            port = _parse_port(cfg_port, "config.yaml:mavlink_out.databus_port")

    if port is None:
        raise ValueError(
            "DataBus destination port is not set. Configure one using either "
            "--databus-port, environment variable DATABUS_PORT, or "
            "config.yaml:mavlink_out.databus_port. "
            "No runtime endpoint discovery is performed."
        )

    if not host:
        raise ValueError(
            "DataBus destination host is not set. Configure one using either "
            "--databus-host, environment variable DATABUS_HOST, or "
            "config.yaml:mavlink_out.databus_host"
        )

    return host, int(port)
