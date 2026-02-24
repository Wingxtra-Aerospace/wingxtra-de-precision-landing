from __future__ import annotations

from ..databus.messages import TYPE_AndruavMessage_INTERNAL_MAVLINK
from ..databus.module import CModule, UdpSendClient
from .base import MavlinkOut


TYPE_ANDRUAVMESSAGE_INTERNAL_MAVLINK = 6504


@dataclass(frozen=True)
class DataBusProtocolKeys:
    """
    Key names used in the DataBus BMSG envelope.

    These are configurable to support DroneEngage deployments that use different
    field aliases in their receiver/parser implementation.
    """

    andruav_message_id: str = "andruav_message_id"
    message_cmd: str = "message_cmd"


class _UdpClient:
    def __init__(self, host: str, port: int, timeout_s: float = 0.05):
        self._addr = (host, int(port))
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.settimeout(float(timeout_s))

    def send(self, payload: bytes) -> None:
        self._sock.sendto(payload, self._addr)


class CModule:
    """Minimal DataBus-style module with BMSG support."""

    def __init__(self, udp_client: _UdpClient, protocol_keys: DataBusProtocolKeys):
        self._udp_client = udp_client
        self._protocol_keys = protocol_keys

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
        bmsg = (
            json.dumps(header, separators=(",", ":")).encode("utf-8")
            + b"\x00"
            + bytes(binary_payload)
        )
        self._udp_client.send(bmsg)


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
