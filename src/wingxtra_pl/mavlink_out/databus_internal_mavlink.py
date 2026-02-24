from __future__ import annotations

import base64
import json
import socket

from .base import MavlinkOut


class DroneEngageDatabusInternalMavlinkOut(MavlinkOut):
    """
    Publishes MAVLink2 packets to DroneEngage over the internal DataBus endpoint.

    The publisher never opens any physical serial port (e.g. /dev/serial0).
    Supported wire formats:
      - udp_raw: sends the MAVLink2 packet bytes as-is
      - udp_json: sends a JSON envelope with a topic + base64 payload
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        transport: str = "udp_raw",
        topic: str = "INTERNAL_MAVLINK",
        timeout_s: float = 0.05,
    ):
        self.host = host
        self.port = port
        self.transport = str(transport)
        self.topic = str(topic)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(float(timeout_s))
        self._addr = (self.host, int(self.port))

        if self.transport not in {"udp_raw", "udp_json"}:
            raise ValueError(
                "Unsupported DataBus transport "
                f"'{self.transport}'. Expected one of: udp_raw, udp_json"
            )

    def send_landing_target(self, mavlink2_packet: bytes) -> None:
        if not isinstance(mavlink2_packet, (bytes, bytearray)):
            raise TypeError("mavlink2_packet must be bytes")
        if not mavlink2_packet:
            return

        if self.transport == "udp_raw":
            payload = bytes(mavlink2_packet)
        else:
            payload = json.dumps(
                {
                    "topic": self.topic,
                    "encoding": "base64",
                    "payload": base64.b64encode(bytes(mavlink2_packet)).decode("ascii"),
                },
                separators=(",", ":"),
            ).encode("utf-8")

        self._sock.sendto(payload, self._addr)
