from __future__ import annotations

import argparse
import json
import socket

INTERNAL_MAVLINK_ID = 6504


def parse_args():
    p = argparse.ArgumentParser(
        description="Fake DataBus RX for INTERNAL MAVLINK validation"
    )
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, required=True)
    return p.parse_args()


def main():
    args = parse_args()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"listening on {args.host}:{args.port}")

    while True:
        data, addr = sock.recvfrom(65535)
        if b"\x00" not in data:
            print(f"{addr} invalid: missing NULL separator")
            continue

        header_raw, payload = data.split(b"\x00", 1)
        try:
            header = json.loads(header_raw.decode("utf-8"))
        except Exception as e:
            print(f"{addr} invalid header json: {e}")
            continue

        msg_id = int(header.get("andruav_message_id", -1))
        msg_cmd = header.get("message_cmd")
        is_internal = msg_id == INTERNAL_MAVLINK_ID
        print(
            f"{addr} id={msg_id} cmd={msg_cmd} payload_len={len(payload)} "
            f"internal_mavlink={is_internal}"
        )


if __name__ == "__main__":
    main()
