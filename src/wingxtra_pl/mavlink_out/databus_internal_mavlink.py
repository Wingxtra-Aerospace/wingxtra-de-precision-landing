from __future__ import annotations

from .base import MavlinkOut


class DroneEngageDatabusInternalMavlinkOut(MavlinkOut):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

        # TODO(Codex): Initialize DroneEngage DataBus client here.
        # Goal: publish INTERNAL MAVLINK messages so de_mavlink forwards them to FC.
        # Keep it strictly "internal" so we use only ONE physical FC MAVLink link.

    def send_landing_target(self, mavlink2_packet: bytes) -> None:
        # TODO(Codex): Publish mavlink2_packet as INTERNAL MAVLINK via DataBus.
        # This plugin MUST NOT open /dev/serial0.
        raise NotImplementedError(
            "Wire this to DroneEngage DataBus INTERNAL_MAVLINK publish"
        )
