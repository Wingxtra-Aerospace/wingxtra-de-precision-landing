from __future__ import annotations

from ..databus.module import CModule, UdpSendClient
from .base import MavlinkOut


class DroneEngageDatabusInternalMavlinkOut(MavlinkOut):
    def __init__(self, host: str, port: int, *, module_key="wingxtra-precision-landing"):
        self.module = CModule(UdpSendClient(host, port), module_key)

    def send_landing_target(self, mavlink2_packet: bytes):
        self.module.sendBMSG(binary_payload=mavlink2_packet)

    def close(self):
        self.module.close()
