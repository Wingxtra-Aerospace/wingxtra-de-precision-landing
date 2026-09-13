#!/usr/bin/env python3
"""Bench-only DataBus wire inspector. Does not forward messages or generate heartbeats."""
import argparse
import json
import socket
from pymavlink.dialects.v20 import common as mavlink

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host', default='127.0.0.1')
parser.add_argument('--port', type=int, default=60001)
args = parser.parse_args()
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
    receiver.bind((args.host, args.port))
    print(f'Bench receiver on {args.host}:{args.port}; not a live DroneEngage service')
    decoder = mavlink.MAVLink(None)
    while True:
        wire, _ = receiver.recvfrom(16384)
        if wire[:2] != b'\xff\xff':
            print('Reject: expected single final DataBus chunk')
            continue
        header, separator, payload = wire[2:].partition(b'\0')
        print(json.loads(header))
        if separator:
            for message in decoder.parse_buffer(payload) or []:
                print(message.to_dict())
