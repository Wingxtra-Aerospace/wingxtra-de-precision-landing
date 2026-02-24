# Printing the Landing Target Sheet (Multi-Tag AprilTag tag36h11)

This project uses a Landmark Landing “Landing Target” export:
- `landing-target.svg` (the printable artwork)
- `landing-target.json` (the layout/geometry file used by our solver)

**Important:** The solver assumes the printed target matches the JSON geometry exactly.
If the print is scaled incorrectly, pose (x/y/z) will be wrong.

---

## 1) Export from Landmark configurator
From the Landmark target configurator, export:
- `landing-target.svg`
- `landing-target.json`

Place both files in the repo root:
- `landing-target.svg` (optional but recommended to keep alongside JSON)
- `landing-target.json` (required)

The JSON includes:
- `family`: `tag36h11`
- tag `id`s
- per-tag `object_points` for the corners (meters) in a shared target coordinate frame.

---

## 2) Print settings (most common failure point)
### Recommended printing method
- Print the SVG at **100% scale (actual size)**.
- Disable “Fit to page”, “Scale to fit”, “Shrink/Expand”.
- If printing from a browser, use a PDF export first and ensure it is still **100%**.

### Paper size
Use the paper size you designed for (A4 / Letter / larger).  
If you made a large target (better for high altitude detection), printing on a larger sheet is preferred.

---

## 3) Verify the print is 1:1 (required)
After printing, use a ruler/tape measure to verify at least one known dimension:

### Option A (best)
If the configurator shows the overall target width/height:
- Measure the printed width/height and confirm it matches.

### Option B (also good)
Measure a tag’s outer black square size on the print and confirm it matches what you designed.

### What to do if it’s off
- If the print is scaled (e.g. 97%, 103%), **do not use it**.
- Reprint with correct settings until the measurement matches.

---

## 4) Mounting the target
- Mount the target on a **flat, rigid backing** (foam board, plywood, acrylic).
- Avoid wrinkles, warping, or glossy reflection.
- If outdoors, protect from wind (flapping ruins detection).

---

## 5) Lighting and contrast tips (IMX219)
- AprilTags need good contrast (solid black on solid white).
- Avoid direct specular reflection (glossy laminate can cause false edges).
- If your target is outdoors, shade it or use matte print.

---

## 6) Camera field-of-view and distance guidance (practical)
Detection at higher altitude depends on the *pixel size* of the large tag.

Rules of thumb:
- Bigger tag = earlier detection.
- Higher resolution = earlier detection (but higher CPU use).
- Too much motion blur = lost detection (use faster shutter / better lighting).

We recommend starting tests at:
- 1280x720 @ 30fps on IMX219
- Then increase resolution only if CPU headroom exists.

---

## 7) Common problems and fixes
### Tag not detected
- Confirm dictionary: this target uses **AprilTag 36h11**
- Ensure OpenCV dictionary is set to `DICT_APRILTAG_36h11`
- Improve lighting / reduce blur
- Ensure target is flat and not reflective
- Confirm print scaling is correct

### Pose jumps / jitter
- Usually caused by:
  - intermittent detection
  - motion blur
  - poor calibration
- Fixes:
  - add pose smoothing in software (EMA/Kalman)
  - reduce speed during final approach
  - improve lighting / shutter speed

### Wrong direction corrections (moves away from pad)
- Axis mapping issue (camera-to-body transform)
- Fix by adjusting `frames.cam_to_body_rpy_deg` or the mapping logic

---

## 8) Safety note
Always test precision landing:
- in GUIDED with manual abort ready
- at low altitude first
- with prop guards or safe test environment where possible
