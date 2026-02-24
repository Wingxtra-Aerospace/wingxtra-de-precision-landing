# Wingxtra Operations Notes – Precision Landing

## Camera Calibration Policy (MANDATORY)
- Every drone + every camera must be calibrated.
- camera.yaml is REQUIRED at runtime.
- camera.yaml must NEVER be committed to Git.
- Recalibrate if:
  - camera is replaced
  - camera is remounted or tilted
  - capture resolution changes

## Generate camera.yaml
1. Print chessboard (9x6 inner corners).
2. Measure square size accurately (meters).
3. Run:
   python3 tools/calibrate_camera.py
4. Verify camera.yaml exists before flight.

## Preflight Checklist
- camera.yaml exists
- config.yaml resolution matches calibration
- landing target printed at 100% scale
- tags are flat, matte, well lit
- dry-run detection tested before flight

## Safety
- First tests at low altitude.
- Abort ready.
- Never fly without confirmed detection.
