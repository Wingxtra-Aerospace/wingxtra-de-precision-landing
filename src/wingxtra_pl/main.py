from __future__ import annotations

import argparse
import os
from pathlib import Path
import time
from typing import Callable, Iterator
import yaml
import numpy as np
import cv2
from picamera2 import Picamera2
from pymavlink.dialects.v20 import common as mavlink2

from .landing_target_layout import LandingTargetLayout
from .vision_multitag import DetectorConfig, MultiTagPoseEstimator
from .transforms import camera_to_body_ned_default, rpy_deg_to_rotmat
from .mavlink_out.databus_internal_mavlink import DroneEngageDatabusInternalMavlinkOut


def load_camera_yaml(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            "Missing required calibration file 'camera.yaml'. "
            "Wingxtra policy requires per-drone calibration. "
            "Run: python3 tools/calibrate_camera.py"
        )

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    K = np.array(data["camera_matrix"]["data"], dtype=float).reshape(3, 3)
    dist = np.array(data["distortion_coefficients"]["data"], dtype=float).reshape(-1, 1)
    image_width = int(data["image_width"])
    image_height = int(data["image_height"])
    return K, dist, image_width, image_height


def build_landing_target_packet(
    *,
    sysid: int,
    compid: int,
    target_num: int,
    x_m: float,
    y_m: float,
    z_m: float,
    angle_x: float,
    angle_y: float,
) -> bytes:
    """
    Creates a MAVLink2 LANDING_TARGET message.
    position_valid=1 so ArduPilot uses x,y,z.
    frame = MAV_FRAME_BODY_NED (8)
    """
    mav = mavlink2.MAVLink(None)
    mav.srcSystem = sysid
    mav.srcComponent = compid

    msg = mavlink2.MAVLink_landing_target_message(
        time_usec=int(time.time() * 1e6),
        target_num=int(target_num),
        frame=8,  # MAV_FRAME_BODY_NED
        angle_x=float(angle_x),
        angle_y=float(angle_y),
        distance=0.0,  # not used when position_valid=1
        size_x=0.0,
        size_y=0.0,
        x=float(x_m),
        y=float(y_m),
        z=float(z_m),
        q=(0.0, 0.0, 0.0, 0.0),  # unused by ArduPilot for this workflow
        type=0,
        position_valid=1,
    )
    # Pack to bytes (MAVLink2)
    pkt = msg.pack(mav)
    return pkt


def parse_args():
    parser = argparse.ArgumentParser(
        description="Wingxtra DroneEngage precision landing"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run vision + pose pipeline without sending MAVLink packets",
    )
    parser.add_argument(
        "--debug-overlay",
        action="store_true",
        help="Show debug overlay window with detections/pose/FPS and optional snapshots",
    )
    parser.add_argument(
        "--save-debug-frames",
        action="store_true",
        help="When used with --debug-overlay, periodically save debug frames to debug_frames/",
    )
    parser.add_argument(
        "--databus-host",
        type=str,
        default=None,
        help="DroneEngage DataBus host override (priority: CLI > ENV > config)",
    )
    parser.add_argument(
        "--databus-port",
        type=int,
        default=None,
        help="DroneEngage DataBus port override (priority: CLI > ENV > config)",
    )
    parser.add_argument(
        "--video",
        type=str,
        default=None,
        help="Read frames from a prerecorded video file instead of Pi camera",
    )
    parser.add_argument(
        "--images",
        type=str,
        default=None,
        help="Read frames from an image directory instead of Pi camera",
    )
    return parser.parse_args()


def _iter_image_dir(path: Path) -> Iterator[np.ndarray]:
    exts = ("*.png", "*.jpg", "*.jpeg", "*.bmp")
    files = []
    for ext in exts:
        files.extend(sorted(path.glob(ext)))
    if not files:
        raise ValueError(f"No images found in directory: {path}")

    for p in files:
        frame = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if frame is None:
            continue
        yield frame


def build_frame_source(
    args, width: int, height: int
) -> tuple[Iterator[np.ndarray], Callable[[], None]]:
    if args.video and args.images:
        raise ValueError("Use only one of --video or --images")

    if args.video:
        cap = cv2.VideoCapture(args.video)
        if not cap.isOpened():
            raise ValueError(f"Unable to open video: {args.video}")

        def gen() -> Iterator[np.ndarray]:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                yield frame

        return gen(), cap.release

    if args.images:
        image_dir = Path(args.images)
        if not image_dir.is_dir():
            raise ValueError(f"--images path is not a directory: {args.images}")
        return _iter_image_dir(image_dir), (lambda: None)

    picam2 = Picamera2()
    video_config = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (width, height)}
    )
    picam2.configure(video_config)
    picam2.start()

    def gen() -> Iterator[np.ndarray]:
        while True:
            frame_rgb = picam2.capture_array()
            yield cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

    return gen(), picam2.stop


def resolve_databus_endpoint(args, cfg):
    cfg_host = cfg["mavlink_out"].get("databus_host")
    cfg_port = cfg["mavlink_out"].get("databus_port")

    host = args.databus_host
    if not host:
        host = os.getenv("DATABUS_HOST") or cfg_host

    env_port_raw = os.getenv("DATABUS_PORT")
    env_port = int(env_port_raw) if env_port_raw else None
    port = args.databus_port if args.databus_port is not None else env_port
    if port is None:
        port = int(cfg_port) if cfg_port is not None else None

    if port is None:
        raise ValueError(
            "DataBus destination port is not set. Configure one using either "
            "--databus-port, environment variable DATABUS_PORT, or "
            "config.yaml:mavlink_out.databus_port"
        )

    if not host:
        raise ValueError(
            "DataBus destination host is not set. Configure one using either "
            "--databus-host, environment variable DATABUS_HOST, or "
            "config.yaml:mavlink_out.databus_host"
        )

    return str(host), int(port)


def main():
    args = parse_args()
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))

    layout = LandingTargetLayout.from_landmark_json(
        cfg["landing_target"]["layout_json"]
    )

    target_num = int(cfg["landing_target"].get("target_num", layout.target_num))

    K, dist, calib_w, calib_h = load_camera_yaml("camera.yaml")

    w = int(cfg["camera"]["width"])
    h = int(cfg["camera"]["height"])
    if calib_w != w or calib_h != h:
        raise ValueError(
            "camera.yaml resolution does not match runtime config. "
            f"calibration={calib_w}x{calib_h}, runtime={w}x{h}. "
            "Use matching config.yaml camera width/height or recalibrate with "
            "python3 tools/calibrate_camera.py"
        )

    estimator = MultiTagPoseEstimator(
        DetectorConfig(opencv_dictionary=cfg["landing_target"]["opencv_dictionary"]),
        layout,
        K,
        dist,
    )

    out = None
    if not args.dry_run:
        databus_host, databus_port = resolve_databus_endpoint(args, cfg)
        out = DroneEngageDatabusInternalMavlinkOut(
            host=databus_host,
            port=databus_port,
            internal_mavlink_cmd=str(
                cfg["mavlink_out"].get("internal_mavlink_cmd", "m")
            ),
        )

    send_hz = float(cfg["mavlink"]["send_hz"])
    period = 1.0 / max(send_hz, 1.0)
    last = 0.0
    last_debug_save = 0.0
    frame_count = 0
    fps_t0 = time.time()
    fps = 0.0

    rpy = cfg["frames"]["cam_to_body_rpy_deg"]
    R_extra = rpy_deg_to_rotmat(float(rpy[0]), float(rpy[1]), float(rpy[2]))

    frame_source, close_source = build_frame_source(args, w, h)

    if args.debug_overlay and args.save_debug_frames:
        Path("debug_frames").mkdir(parents=True, exist_ok=True)
    elif args.save_debug_frames:
        print("--save-debug-frames has no effect without --debug-overlay")

    if args.dry_run:
        print("Running in --dry-run mode: no MAVLink output will be sent")

    # MAVLink identity for the companion/plugin
    SYSID = 42
    COMPID = 191

    for frame_bgr in frame_source:

        res = estimator.estimate(frame_bgr)
        now = time.time()
        frame_count += 1
        dt = now - fps_t0
        if dt >= 1.0:
            fps = frame_count / dt
            frame_count = 0
            fps_t0 = now

        overlay = frame_bgr.copy() if args.debug_overlay else None

        if res and (now - last) >= period:
            tvec_cam = res["tvec"]
            body = camera_to_body_ned_default(tvec_cam)
            body = (R_extra @ body.reshape(3, 1)).reshape(3)

            pkt = build_landing_target_packet(
                sysid=SYSID,
                compid=COMPID,
                target_num=target_num,
                x_m=float(body[0]),
                y_m=float(body[1]),
                z_m=float(body[2]),
                angle_x=float(res["angle_x"]),
                angle_y=float(res["angle_y"]),
            )

            print(
                "used_ids=%s markers=%d x=%.3f y=%.3f z=%.3f"
                % (
                    res["used_ids"],
                    res["num_markers_used"],
                    float(body[0]),
                    float(body[1]),
                    float(body[2]),
                )
            )

            # Forward to DroneEngage (single FC link)
            if not args.dry_run:
                out.send_landing_target(pkt)

            last = now

        if args.debug_overlay:
            corners, ids, _ = estimator.detector.detectMarkers(frame_bgr)
            if ids is not None and len(ids) > 0:
                cv2.aruco.drawDetectedMarkers(overlay, corners, ids)

            if res:
                tvec_cam = res["tvec"]
                body = camera_to_body_ned_default(tvec_cam)
                body = (R_extra @ body.reshape(3, 1)).reshape(3)
                lines = [
                    f"used_ids: {res['used_ids']}",
                    f"num_markers_used: {res['num_markers_used']}",
                    f"x: {float(body[0]):.3f} m",
                    f"y: {float(body[1]):.3f} m",
                    f"z: {float(body[2]):.3f} m",
                ]
            else:
                lines = [
                    "used_ids: []",
                    "num_markers_used: 0",
                    "x: n/a",
                    "y: n/a",
                    "z: n/a",
                ]

            lines.append(f"FPS: {fps:.1f}")
            if args.dry_run:
                lines.append("MODE: DRY RUN")

            for i, line in enumerate(lines):
                y = 30 + i * 28
                cv2.putText(
                    overlay,
                    line,
                    (15, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA,
                )

            cv2.imshow("Wingxtra Precision Landing Debug", overlay)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

            if args.save_debug_frames and (now - last_debug_save) >= 2.0:
                cv2.imwrite(f"debug_frames/frame_{int(now * 1000)}.jpg", overlay)
                last_debug_save = now

        time.sleep(0.001)

    close_source()
    if args.debug_overlay:
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
