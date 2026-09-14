"""Small, send-only implementation of DroneEngage's documented UDP framing.

Wire format reference: DroneEngage/droneengage_databus python/de_module.py,
python/messages.py and python/udpClient.py. Landing packets fit one chunk.
"""

from __future__ import annotations

import json
import socket
import time


class UdpSendClient:
    def __init__(self, host: str, port: int, timeout_s=0.05):
        self.address = (host, int(port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(timeout_s)

    def send(self, payload: bytes):
        if len(payload) > 8192:
            raise ValueError("DataBus landing messages must fit one chunk")
        self.socket.sendto(b"\xff\xff" + payload, self.address)

    def close(self):
        self.socket.close()


class CModule:
    def __init__(self, udp_client: UdpSendClient, module_key="wingxtra-precision-landing"):
        self.client = udp_client
        self.key = module_key
        self.instance_time = time.time()
        self.last_registration = -float("inf")

    def register(self, now=None):
        now = time.monotonic() if now is None else now
        if now - self.last_registration < 1:
            return
        message = {
            "ty": "uv",
            "mt": 9100,
            "ms": {
                "a": "wingxtra-precision-landing",
                "b": "gen",
                "c": [],
                "d": ["T"],
                "e": self.key,
                "v": "1.0.0-rc.1",
                "z": True,
                "u": self.instance_time,
            },
        }
        self.client.send(json.dumps(message, separators=(",", ":")).encode())
        self.last_registration = now

    def sendBMSG(self, *, andruav_message_id=6504, message_cmd=None, binary_payload: bytes):
        if not isinstance(binary_payload, bytes) or not binary_payload:
            raise ValueError("A non-empty MAVLink packet is required")
        self.register()
        header = {
            "GU": self.key,
            "tg": "",
            "ty": "uv",
            "mt": andruav_message_id,
            "ms": {} if message_cmd is None else message_cmd,
        }
        self.client.send(
            json.dumps(header, separators=(",", ":")).encode() + b"\0" + binary_payload
        )

    def close(self):
        self.client.close()
