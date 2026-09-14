# Landmark boot-data review

Evidence record **LMBOOT-001** · 2026-09-14 · B01, REF01, F05, T02, T16, O10.

The user supplied a ZIP copied from the boot side of a working Landmark SD card. It supports a limited configuration/data comparison and has exposed a reproducible Wingxtra vision failure. It does **not** provide a code-to-code comparison or independent validation of either system's aircraft behaviour.

Wingxtra reference: main [`ab2f242790d324ef030602f0aa2a5bcbf940f8c5`](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/commit/ab2f242790d324ef030602f0aa2a5bcbf940f8c5), tree `eca9ec66c54f47ccdbaf63b147d92c5b6a8a06a3`. Local diagnostic environment: **Python 3.12.14, NumPy 2.5.3, OpenCV 4.13.0**, using the repository's declared pip vision dependency. The diagnostic was not executed inside the Debian OpenCV image or on the selected CM4.

## Supplied evidence

The original archive remains in the user's conversation attachment, outside this public source tree. Its contents were read without execution or modification. No private matrices, corner coordinates, licence values or application files are included here.

| Input | SHA-256 |
|---|---|
| `Precision landing.zip` | `9f51f6bb9bf9588a5a16ff8735bd1409e5da9be1574792db05ed5bfdfabd7c37` |
| `New folder/camera_calibration.json` | `9cfe618ad2cace352f2e116844be75d1aef838a456338fb8ec662d2cfa2e80d8` |
| `New folder/marker_layouts/a4_max.json` | `fa9ba9aa6e625c7f2821bc9007b801ec41e5460c1a01301acd9b048e2ab07395` |
| `New folder/marker_layouts/fibonacci.json` | `dd3911b103c699d01d2e10a8cd21b963477f1c15c3892bb1b2e713442cd3d257` |

The ZIP has **404 files and three directory entries**, totalling **39,412,344 uncompressed bytes**. ZIP CRC validation passes. Most entries are Raspberry Pi boot firmware/device trees/overlays. The four JSON files comprise calibration, two marker layouts and a licence record. Licence values are excluded from this review.

Both `initramfs8` and `initramfs_2712` were decompressed in memory and their CPIO inventories inspected, including boot-script text searches. Each contains 446 CPIO entries with generic boot utilities/scripts; no Landmark application was located. No Python application files, Landmark startup service, flight-controller parameter dump, recorded camera observations or landing logs were found in the supplied files. `config.txt`, `cmdline.txt` and the usual kernel image filenames are also absent: this ZIP is not a complete bootable disk image.

`issue.txt` identifies a Raspberry Pi reference image dated 2025-05-13. That is a base-image reference, not a verified application version, calibration date or current kernel version. Camera overlays and board device trees do not identify the connected camera or hardware. The application may be on the missing Linux root filesystem, and may be supplied as a binary rather than source.

## Data compatibility

| Item | Observation | Result with current Wingxtra |
|---|---|---|
| A4 layout | Four `tag36h11` markers with unique IDs and consistent planar square geometry | `LandingTargetLayout.from_dict` accepts all four without modification. Estimator robustness is separately failing as recorded below. |
| Fibonacci layout | Fifteen `tag36h11` markers with consistent square geometry | Loader rejects marker 114 at the existing maximum marker-edge check. Its edge value is 6.1, exceeding 5 m under Wingxtra's metre interpretation. The error text says the points must describe a square in metres; the failing condition is the size guard, not non-square geometry. |
| Calibration | Saved image dimensions 3280×2464; camera matrix; five distortion coefficients; `ret`; 169 rotation/translation-vector pairs | `Calibration.model_validate` rejects the foreign schema. No Wingxtra camera fingerprint, accepted-view quality metadata or creation timestamp is supplied. `CameraConfig(width=3280, height=2464)` also exceeds the current 2160-pixel height limit. |
| Active setup | Two layouts and calibration data, without the runtime selection/configuration | Cannot determine which board, video mode, camera, altitude source, gimbal mode or MAVLink settings were in use. |

The relevant implementation is pinned in [layout validation](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/ab2f242790d324ef030602f0aa2a5bcbf940f8c5/src/wingxtra_pl/landing_target_layout.py), [calibration validation](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/ab2f242790d324ef030602f0aa2a5bcbf940f8c5/src/wingxtra_pl/calibration.py) and [camera configuration](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/ab2f242790d324ef030602f0aa2a5bcbf940f8c5/src/wingxtra_pl/config.py).

The board JSON does not explicitly declare units. The comparisons use Wingxtra's existing metre convention; no physical measurement confirms the user's printed board or a 6.1 m marker. The Fibonacci file may be a general template. Do not rescale it or remove markers merely to pass validation.

The saved calibration resembles OpenCV output, but its producer code is absent. The 169 vector pairs are not flight evidence and cannot supply Wingxtra's required per-view reprojection errors without the corresponding observations. Renaming keys is insufficient; inventing quality/identity fields or scaling the matrix without a verified crop/resize model is not a valid conversion. A fresh calibration at the intended supported stream remains the supported path. These files do not identify a camera model or demonstrate performance at full resolution.

## Licence and portability question

The user asked whether the card is tied to its original Raspberry Pi. The licence JSON has `serial` and `signature` fields; `serial` is a 16-character hexadecimal string. This is consistent with the hardware serial format shown in [Raspberry Pi's official documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#raspberry-pi-revision-codes). It suggests a device-bound signed licence, but does not establish what Landmark actually verifies. No licence-checking code or transfer policy was found in the supplied files; the examined Landmark product page and public tutorial do not settle it.

If validation binds the licence to the Pi's hardware serial, copying a full card preserves the licence for the original Pi but does not transfer that hardware identity to another Pi. Additional checks could exist, so operation even on a replacement card is not tested here. Comparing the licence's serial privately with the original Pi's `Serial` line in `/proc/cpuinfo` can strengthen that identification; inspecting the installed verifier or obtaining vendor confirmation is needed to confirm enforcement and transfer support. No licence modification, execution on another device or transfer attempt was performed. This does not block read-only comparison of the supplied files.

## Synthetic pose rejection

**B01 is reopened.** The [shared estimator](https://github.com/Wingxtra-Aerospace/wingxtra-de-precision-landing/blob/ab2f242790d324ef030602f0aa2a5bcbf940f8c5/src/wingxtra_pl/vision_multitag.py) rejects internally consistent, noiseless multi-tag observations on the inspected pip OpenCV build. This failure can affect either fixed or gimbal mode because it occurs before camera-to-body transformation.

Reproduction recipe for a reviewer with authorised access to the hashed attachment:

1. Use the pinned Wingxtra source and environment above. Read the A4 JSON unchanged through `LandingTargetLayout.from_dict`, retaining its marker order. Read the calibration matrix as float64 and flatten its five distortion coefficients. Use these numeric inputs directly in `MultiTagPoseEstimator(DetectorConfig(), layout, K, distortion)`. This diagnostic does not claim that the service accepts the foreign calibration file.
2. Use float64 Rodrigues rotation vector `[pi - 0.18, 0.05, 0.02]` and translation `[0.04, -0.02, depth]`. These are generated camera-frame inputs; `depth` is camera Z, not an aircraft altitude measurement.
3. For each marker, generate the four exact image corners with `cv2.projectPoints` from the unchanged board coordinates. Supply corners as `(1, 4, 2)` arrays and IDs as an int32 `(4, 1)` array to `estimate_corners`.
4. Test depths `0.5, 1.0, 2.0, 4.0` and reset `cv2.setRNGSeed` separately to `1, 2, 3` at each depth. Every case has positive point depths and all corners inside the declared 3280×2464 image. The minimum projected edge exceeds the existing 12 px threshold.
5. Trace the prefilter by resetting the same seed and calling `solvePnPRansac` with all 16 float64 points, `SOLVEPNP_EPNP`, 100 iterations, 3 px reprojection error and confidence 0.999. Apply the production requirement that all four corners of a retained tag be inliers and at least two tags remain.
6. As a diagnostic control only, call `solvePnPGeneric` with all original points and `SOLVEPNP_IPPE`. Exclude nonpositive-depth solutions and evaluate pixel RMS against those same observations. This control isolates the rejection stage; bypassing outlier rejection is not an implemented or accepted fix.

Each row below has the same result for all three seeds:

| Synthetic depth (m) | Minimum edge (px) | EPNP-RANSAC corner inliers | Complete retained tags | Wingxtra result | Direct IPPE, all points: best RMS (px) |
|---|---|---|---|---|---|
| 0.5 | 205.589 | 0; returns false | 0 | No pose | 3.82e-8 |
| 1.0 | 104.540 | 7 | 0 | No pose | 1.93e-10 |
| 2.0 | 52.879 | 15 | 3 | Pose using three tags | 1.50e-13 |
| 4.0 | 26.624 | 16 | 4 | Pose using all four tags | 8.04e-14 |

Thus **six of twelve depth/seed cases return no pose**, and only three use all four valid tags. Direct IPPE recovers the known translation with error no greater than `4.56e-11 m` in these noiseless controls. The failure occurs in the RANSAC/whole-tag prefilter, before the final IPPE stage can assess the complete consistent board. This diagnosis does not establish whether an underlying OpenCV implementation detail contributes; the observable Wingxtra failure is reproducible in its declared pip environment.

Additional limited observations during inspection: at synthetic depth 1.5 m, each of the four tags individually recovers the common origin, while the joint estimator retains only two. A rendered-image check using the existing test helper at 1280×720, zero distortion and focal lengths 900 px detects all four tags, retains three and has approximately 0.0118 m translation error. These are synthetic diagnostic measurements, not camera/aircraft accuracy claims, replay of Landmark images or an accepted operating envelope.

Earlier CI and rendered-image checks are not withdrawn for their original cases. The new inputs show that those checks did not cover this mixed-size board failure. No implementation or regression test has been changed in this review. The correction must handle valid planar/mixed-size observations while preserving resistance to incorrect IDs/corners, contradictory tags and planar ambiguity, and must be checked in both the pip and Debian OpenCV environments. Physical scale and camera validation remain separate gates.

## Remaining inputs

REF01/T16 cannot yet compare the landing algorithms. The next useful material is a copy of the card's **Linux root filesystem**, or a full disk image containing all partitions. Alternatively, supply the installed Landmark application directory, its startup service and configuration; the actual path must be discovered from that system. A disk image does not guarantee that source code was distributed.

Also retain the active board/configuration, camera and firmware identity, measured printed dimensions, flight-controller firmware/parameters, and recorded images plus corresponding messages/logs from a known successful run. These establish what was actually running and make a fair replay or measured comparison possible. Keep the original working card unchanged and retain private reference contents outside the public repository.

This upload establishes the presence of multi-tag board definitions, not proof that Landmark jointly fits every visible tag, how it derives distance without a rangefinder, how it handles gimbal motion, or how the aircraft behaves on target loss. Those questions remain open. The immediate Wingxtra action is the B01/T02 correction; missing Landmark source does not prevent it.
