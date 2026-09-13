from __future__ import annotations

import argparse
import os
from pathlib import Path

import uvicorn
import yaml
import cv2

from .config import Config
from .legacy_cli import resolve_databus_endpoint
from .service import LandingService
from .web import create_app


def main():
    parser = argparse.ArgumentParser(description="Wingxtra Precision Landing / BlueOS extension")
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("PL_DATA_DIR", "./data")))
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--databus-host", help="DataBus host: CLI > DATABUS_HOST > config")
    parser.add_argument(
        "--databus-port", type=int, help="DataBus port: CLI > DATABUS_PORT > config"
    )
    parser.add_argument("--port", type=int, default=int(os.getenv("PL_WEB_PORT", "8077")))
    parser.add_argument(
        "--config", type=Path, help="Import a schema-version-1 YAML/JSON configuration"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Start in monitor mode; no target output"
    )
    args = parser.parse_args()
    cv2.setNumThreads(2)
    service = LandingService(args.data_dir)
    incoming = (
        Config.model_validate(yaml.safe_load(args.config.read_text())) if args.config else None
    )
    if (
        args.databus_host
        or args.databus_port
        or os.getenv("DATABUS_HOST")
        or os.getenv("DATABUS_PORT")
    ):
        incoming = incoming or service.config.model_copy(deep=True)
        host, port = resolve_databus_endpoint(args, {"mavlink_out": incoming.output.model_dump()})
        incoming.output.databus_host, incoming.output.databus_port = host, port
        incoming.output.mode = "droneengage_databus"
    if incoming:
        service.update_config(incoming)
        # update_config opens the listener; startup owns opening it once.
        if service.link:
            service.link.close()
            service.link = None
        if service.databus:
            service.databus.close()
            service.databus = None
    if args.dry_run:
        service.output_inhibited = True
        service.config.startup_mode = "monitor"
    uvicorn.run(
        create_app(args.data_dir, service),
        host=args.host,
        port=args.port,
        access_log=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
