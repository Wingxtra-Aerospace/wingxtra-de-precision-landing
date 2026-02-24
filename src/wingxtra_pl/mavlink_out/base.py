from __future__ import annotations
from abc import ABC, abstractmethod


class MavlinkOut(ABC):
    @abstractmethod
    def send_landing_target(self, mavlink2_packet: bytes) -> None:
        """Send a fully encoded MAVLink2 packet to DroneEngage for forwarding to the FC."""
        raise NotImplementedError
