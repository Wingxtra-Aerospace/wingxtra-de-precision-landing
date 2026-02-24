# Wingxtra Operations Notes

## Mandatory per-drone camera calibration policy

- Every **drone + camera + mounting/resolution combination** must have its own `camera.yaml`.
- `camera.yaml` is aircraft-specific configuration and **must never be committed**.
- The runtime must fail fast if `camera.yaml` is missing or resolution mismatches `config.yaml`.

## How to generate `camera.yaml`

1. SSH into the DroneEngage Raspberry Pi.
2. Open this repo on that Pi.
3. Print a chessboard calibration sheet (10x7 squares, 9x6 inner corners).
4. Measure square size and set `SQUARE_SIZE_M` in `tools/calibrate_camera.py`.
5. Run:

```bash
python3 tools/calibrate_camera.py
```

6. Confirm `camera.yaml` is created locally and not tracked by git.

## What triggers recalibration

Recalibrate whenever any of these change:

- camera module replaced
- focus changed
- camera position/orientation remounted
- lens or holder changed
- resolution changed (`config.yaml` width/height)
- significant vibration/mechanical change around camera mount

## Preflight checklist

- `camera.yaml` exists on drone.
- `camera.yaml` resolution matches `config.yaml` camera width/height.
- `landing-target.json` present and correct for deployed target.
- `opencv_dictionary` is `DICT_APRILTAG_36h11`.
- DroneEngage DataBus host/port are correct for that vehicle.
- Start in `--dry-run --debug-overlay` and verify stable detections (`used_ids`, `x/y/z`, FPS).
- Verify no process in this module touches `/dev/serial0`.

## Safety warnings

- This module must **not** open FC serial ports; DroneEngage owns the physical MAVLink link.
- Never fly precision landing with stale/missing/wrong calibration.
- Validate axis mapping and signs in a controlled environment before flight.
- Treat first runs as test-only until LANDING_TARGET values are stable and consistent.
