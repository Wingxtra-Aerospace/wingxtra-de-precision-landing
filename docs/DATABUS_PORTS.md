# DroneEngage DataBus transport

On BlueOS prefer the normal UDP transport: BlueOS owns the FC serial link, and both this extension and DroneEngage connect to separate router endpoints. DataBus is an advanced native integration option, not needed for the BlueOS extension.

Set `output.mode=droneengage_databus`, the actual local DataBus host/port, and a unique module key. Port 60000 is only an example default. The installed DroneEngage communicator configuration is authoritative. Native CLI `--databus-host/--databus-port` take precedence over `DATABUS_HOST/DATABUS_PORT`, which take precedence over the saved configuration; supplying these overrides selects DataBus output.

The application emits a module registration (message 9100) at most once per second while sending, followed by INTERNAL_MAVLINK (6504) messages. The message envelope uses `GU`, `tg`, `ty="uv"`, `mt` and `ms`; binary MAVLink follows a null separator. A single UDP message starts with the little-endian final-chunk bytes `ff ff`. The earlier long-form JSON field aliases and missing chunk prefix were not the upstream wire format.

This minimal client is send-only. Registration is not proof that a DroneEngage communicator accepted or forwarded the message. Live forwarding must be verified against the installed communicator/mavlink module versions. It does not perform remote/cloud routing and does not open an FC serial port.

A **separate raw MAVLink telemetry feed** must reach this application's configured UDP listen endpoint. The normal system/component-1 ArduPilot heartbeat supervises output and tracks armed state. DataBus JSON does not count as a heartbeat. Missing telemetry suppresses output even if the DataBus destination accepts UDP.

Bench protocol inspection is available through `python tools/fake_databus_rx.py --port 60001`. This prints registration and decoded MAVLink packets; it is not a DroneEngage server, does not generate a fake autopilot heartbeat and does not forward traffic to the aircraft.

Reference: [upstream module and UDP client](https://github.com/DroneEngage/droneengage_databus/tree/main/python). See tests for an actual UDP wire-format check.
