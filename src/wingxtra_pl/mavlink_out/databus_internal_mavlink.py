from __future__ import annotations

from ..databus.messages import TYPE_AndruavMessage_INTERNAL_MAVLINK
from ..databus.module import CModule, UdpSendClient
from .base import MavlinkOut


class DroneEngageDatabusInternalMavlinkOut(MavlinkOut):
    """
    Sends INTERNAL MAVLINK packets to DroneEngage via DataBus BMSG over UDP.

    This class never opens /dev/serial0 (or any FC physical MAVLink link).
    """

    def __init__(
        self,
        host: str,
        port: int,
        *,
        internal_mavlink_cmd: str = "m",
        andruav_message_id: int = TYPE_AndruavMessage_INTERNAL_MAVLINK,
    ):
        self.host = host
        self.port = int(port)
        self.internal_mavlink_cmd = str(internal_mavlink_cmd)
        self.andruav_message_id = int(andruav_message_id)

        self._module = CModule(UdpSendClient(self.host, self.port))

    def send_landing_target(self, mavlink2_packet: bytes) -> None:
        if not isinstance(mavlink2_packet, (bytes, bytearray)):
            raise TypeError("mavlink2_packet must be bytes")
        if not mavlink2_packet:
            return

        self._module.sendBMSG(
            andruav_message_id=self.andruav_message_id,
            message_cmd=self.internal_mavlink_cmd,
            binary_payload=bytes(mavlink2_packet),
        )
