# Wingxtra Precision Landing – Architecture Overview

This document explains **why this architecture exists**, how components interact,
and what must **never be changed**.

This is required reading for all new Wingxtra engineers.

---

## High-Level Goal

Run **precision landing** and **DroneEngage** on a **single Raspberry Pi**
using **one MAVLink connection to the flight controller**, with zero conflicts.

---

## One-Page Architecture Diagram

              ┌─────────────────────────────┐
              │        Ground Control        │
              │ (Mission Planner / QGC / UI) │
              └─────────────▲───────────────┘
                            │ MAVLink
                            │
               ┌────────────┴─────────────┐
               │      Flight Controller     │
               │   (ArduPilot / PX4)        │
               └────────────▲─────────────┘
                            │
                            │ SERIAL / USB (ONE PORT ONLY)
                            │
    ┌───────────────────────┴────────────────────────┐
    │               Raspberry Pi (Single Board)       │
    │                                                  │
    │  ┌──────────────────────────────────────────┐  │
    │  │            DroneEngage Core               │  │
    │  │                                          │  │
    │  │  - de_comm (DataBus router)               │  │
    │  │  - de_mavlink (owns FC serial port)       │  │
    │  │  - WebClient / Telemetry                  │  │
    │  └───────────────▲──────────────────────────┘  │
    │                  │ DataBus (UDP, internal)      │
    │                  │                              │
    │  ┌───────────────┴──────────────────────────┐  │
    │  │  Wingxtra Precision Landing Plugin         │  │
    │  │                                          │  │
    │  │  - Camera (IMX219)                         │  │
    │  │  - AprilTag detection (multi-size)         │  │
    │  │  - solvePnP pose estimation                │  │
    │  │  - Builds LANDING_TARGET MAVLink           │  │
    │  │  - SEND ONLY via DataBus                   │  │
    │  └──────────────────────────────────────────┘  │
    │                                                  │
    └──────────────────────────────────────────────────┘

    
---

## Key Rules (Non-Negotiable)

### Rule 1 — One MAVLink Port Only
- The **flight controller has exactly ONE MAVLink connection**.
- `de_mavlink` is the **only** component allowed to open it.
- No plugin may ever open `/dev/serial0` or `/dev/ttyUSB*`.

**Why:**  
Multiple processes opening the same port causes packet corruption and unsafe behavior.

---

### Rule 2 — Precision Landing Is Send-Only
- The precision landing plugin:
  - **does not listen**
  - **does not bind**
  - **does not sniff**
- It only **publishes** `INTERNAL_MAVLINK` messages to DroneEngage DataBus.

**Why:**  
This prevents UDP port conflicts and removes the need for privileged sockets.

---

### Rule 3 — No Hardcoded Ports
- DataBus destination port is **deployment-specific**.
- It must be provided via:
  1. CLI arguments
  2. Environment variables
  3. config.yaml

If no port is provided:
- the program **fails fast**.

**Why:**  
Wingxtra has already experienced failures caused by assuming ports like 6000 or 60000.

---

### Rule 4 — camera.yaml Is Mandatory Per Drone
- Every drone and every camera must have its own `camera.yaml`.
- `camera.yaml` is required at runtime.
- `camera.yaml` must NEVER be committed to Git.

**Why:**  
Camera calibration is hardware-specific and directly affects landing accuracy.

---

## Data Flow Summary

1. Camera captures image
2. AprilTags detected (any subset of large / medium / small)
3. Multi-tag corners fused into one pose
4. Pose smoothed and validated
5. LANDING_TARGET MAVLink packet created
6. Packet sent via DataBus as INTERNAL MAVLink
7. DroneEngage forwards to flight controller

---

## What This Architecture Prevents

- ❌ Serial port contention
- ❌ UDP bind conflicts
- ❌ “It works on my drone” bugs
- ❌ Multiple Raspberry Pi boards per aircraft
- ❌ Hidden coupling between plugins

---

## What Must Never Be Changed

- Do NOT add serial access to this plugin
- Do NOT add UDP listeners
- Do NOT add packet sniffing
- Do NOT hardcode ports
- Do NOT bypass DroneEngage DataBus

If any of the above seems necessary, the architecture is being violated and must be reviewed.

---

## Summary (Read This If You Skip Everything Else)

> **DroneEngage owns communication.  
> Precision landing computes intelligence.  
> DataBus connects them safely.**

This separation is intentional and required for Wingxtra fleet safety.
