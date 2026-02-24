from __future__ import annotations

import json
import socket
from dataclasses import dataclass


@dataclass(frozen=True)
class DataBusProtocolKeys:
    andruav_message_id: str = "andruav_message_id"
    message_cmd: str = "message_cmd"


class UdpSendClient:
    """Send-only UDP client for DataBus payload emission."""

    def __init__(self, host: str, port: int, timeout_s: float = 0.05):
        self._addr = (host, int(port))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(float(timeout_s))

    def send(self, payload: bytes) -> None:
        self._sock.sendto(payload, self._addr)


class CModule:
    """Minimal DataBus-compatible module that implements sendBMSG."""

    def __init__(
        self,
        udp_client: UdpSendClient,
        protocol_keys: DataBusProtocolKeys | None = None,
    ):
        self._udp_client = udp_client
        self._protocol_keys = protocol_keys or DataBusProtocolKeys()

    def sendBMSG(
        self,
        *,
        andruav_message_id: int,
        message_cmd: str,
        binary_payload: bytes,
    ) -> None:
        if not isinstance(binary_payload, (bytes, bytearray)):
            raise TypeError("binary_payload must be bytes")
        if not message_cmd:
            raise ValueError("message_cmd must be a non-empty string")

        header = {
            self._protocol_keys.andruav_message_id: int(andruav_message_id),
            self._protocol_keys.message_cmd: str(message_cmd),
        }
        wire = (
            json.dumps(header, separators=(",", ":")).encode("utf-8")
            + b"\x00"
            + bytes(binary_payload)
        )
        self._udp_client.send(wire)
