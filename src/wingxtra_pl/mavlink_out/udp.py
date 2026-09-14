"""MAVLink 2 encoder and a router endpoint. Never owns a serial port or emits a heartbeat."""

from __future__ import annotations

import math
import socket
import struct
import sys
import time

import numpy as np
from pymavlink.dialects.v20 import common as mavlink

from ..config import OutputConfig


class LandingTargetEncoder:
    def __init__(self, system_id=1, component_id=193):
        self.mav = mavlink.MAVLink(None, srcSystem=system_id, srcComponent=component_id)

    def encode(self, position, captured_unix_us: int, target_num=0) -> bytes:
        p = np.asarray(position, dtype=float)
        if p.shape != (3,) or not np.isfinite(p).all() or p[2] <= 0:
            raise ValueError("Landing target must be finite and below the aircraft")
        distance = float(np.linalg.norm(p))
        if not 0 < distance <= 100 or captured_unix_us <= 0:
            raise ValueError("Invalid target distance or capture timestamp")
        # Full position, camera origin, expressed in vehicle forward/right/down axes.
        msg = mavlink.MAVLink_landing_target_message(
            time_usec=int(captured_unix_us),
            target_num=target_num,
            frame=mavlink.MAV_FRAME_BODY_FRD,
            angle_x=math.atan2(p[1], p[2]),
            angle_y=math.atan2(-p[0], p[2]),
            distance=distance,
            size_x=0,
            size_y=0,
            x=p[0],
            y=p[1],
            z=p[2],
            q=[1, 0, 0, 0],
            type=mavlink.LANDING_TARGET_TYPE_VISION_FIDUCIAL,
            position_valid=1,
        )
        packet = msg.pack(self.mav)
        self.mav.seq = (self.mav.seq + 1) % 256
        return packet


class RouterLink:
    # Linux UAPI asm-generic/socket.h; NEW uses two int64 fields on both architectures.
    # Python does not expose this constant on every supported build.
    RX_TIMESTAMP_NS = 64  # SO_TIMESTAMPNS_NEW, Linux >= 5.1

    def __init__(self, config: OutputConfig):
        self.config = config
        self.allowed_ip = socket.gethostbyname(config.peer_host)
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            if sys.platform != "linux":
                raise OSError("MAVLink receive timestamps require Linux")
            self.socket.setsockopt(socket.SOL_SOCKET, self.RX_TIMESTAMP_NS, 1)
            # Deliberately no SO_REUSEADDR: two senders must not share this endpoint.
            self.socket.bind((config.listen_host, config.listen_port))
            self.socket.setblocking(False)
        except Exception:
            self.socket.close()
            raise
        self.peer = None
        self.last_heartbeat = None
        self.armed = None
        self.seen_heartbeat = False
        self.backlogged = False
        self.sent = 0

    def poll(self, now=None):
        now = time.monotonic() if now is None else now
        self.backlogged = False
        for _ in range(64):
            try:
                data, ancillary, flags, peer = self.socket.recvmsg(65535, socket.CMSG_SPACE(16))
            except BlockingIOError:
                break
            if peer[0] != self.allowed_ip or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                continue
            received_ns = None
            for level, kind, value in ancillary:
                if level == socket.SOL_SOCKET and kind == self.RX_TIMESTAMP_NS and len(value) >= 16:
                    seconds, nanos = struct.unpack("=qq", value[:16])
                    received_ns = seconds * 1_000_000_000 + nanos
            if received_ns is None:
                continue  # A datagram without a trustworthy receive age cannot authorize output.
            age = (time.time_ns() - received_ns) / 1_000_000_000
            received = now - age
            if self.peer is not None and peer != self.peer and self.fresh(now):
                continue
            # Routers send complete messages per datagram. Never join an old partial
            # message to newer bytes and attribute the new packet's timestamp to it.
            parser = mavlink.MAVLink(None)
            parser.robust_parsing = True
            try:
                messages = parser.parse_buffer(data) or []
            except (ValueError, mavlink.MAVError):
                continue
            for msg in messages:
                if (
                    msg.get_type() == "HEARTBEAT"
                    and msg.get_srcSystem() == self.config.target_system
                    and msg.get_srcComponent() == mavlink.MAV_COMP_ID_AUTOPILOT1
                    and msg.autopilot == mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA
                ):
                    self.seen_heartbeat = True
                    if not 0 <= age <= self.config.heartbeat_timeout_s:
                        continue
                    if self.last_heartbeat is not None and received < self.last_heartbeat:
                        continue
                    self.peer = peer
                    self.last_heartbeat = received
                    self.armed = bool(msg.base_mode & mavlink.MAV_MODE_FLAG_SAFETY_ARMED)
        else:
            # A pending newer armed/lost-link state must not be hidden behind telemetry.
            self.backlogged = True

    def fresh(self, now=None):
        now = time.monotonic() if now is None else now
        return (
            self.last_heartbeat is not None
            and not self.backlogged
            and 0 <= now - self.last_heartbeat <= self.config.heartbeat_timeout_s
        )

    def send(self, packet: bytes, now=None) -> bool:
        if not self.fresh(now) or self.peer is None:
            return False
        self.socket.sendto(packet, self.peer)
        self.sent += 1
        return True

    def status(self, now=None):
        now = time.monotonic() if now is None else now
        return {
            "connected": self.fresh(now),
            "armed": self.armed,
            "heartbeat_age_s": None
            if self.last_heartbeat is None
            else (round(now - self.last_heartbeat, 2)),
            "peer": list(self.peer) if self.peer else None,
            "sent": self.sent,
            "backlogged": self.backlogged,
        }

    def close(self):
        self.socket.close()
