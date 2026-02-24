from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
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
        "--databus-sniff",
        action="store_true",
        help="Infer active DataBus UDP port by probing/sniffing candidates",
    )
    parser.add_argument(
        "--databus-sniff-ports",
        type=str,
        default=None,
        help="Comma-separated UDP ports for --databus-sniff (e.g. '60000,60001')",
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
        discovered = discover_databus_endpoint(args, cfg, allow_probe=args.databus_sniff)
        if discovered:
            host = host or discovered[0]
            port = discovered[1]

    if port is None:
        raise ValueError(
            "DataBus destination port is not set. Configure one using either "
            "--databus-port, environment variable DATABUS_PORT, or "
            "config.yaml:mavlink_out.databus_port. Optionally use --databus-sniff"
        )

    if not host:
        raise ValueError(
            "DataBus destination host is not set. Configure one using either "
            "--databus-host, environment variable DATABUS_HOST, or "
            "config.yaml:mavlink_out.databus_host"
        )

    return str(host), int(port)


def _candidate_ports(args, cfg) -> list[int]:
    ports: list[int] = []

    if args.databus_sniff_ports:
        for p in args.databus_sniff_ports.split(","):
            p = p.strip()
            if p:
                ports.append(int(p))

    cfg_candidates = cfg["mavlink_out"].get("databus_candidate_ports", [])
    for p in cfg_candidates:
        ports.append(int(p))

    env_candidates = os.getenv("DATABUS_CANDIDATE_PORTS", "")
    if env_candidates:
        for p in env_candidates.split(","):
            p = p.strip()
            if p:
                ports.append(int(p))

    seen = set()
    unique = []
    for p in ports:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _candidate_hosts(args, cfg) -> list[str]:
    hosts = [
        args.databus_host,
        os.getenv("DATABUS_HOST"),
        cfg["mavlink_out"].get("databus_host"),
    ]
    unique: list[str] = []
    seen = set()
    for h in hosts:
        if h and h not in seen:
            seen.add(h)
            unique.append(str(h))
    return unique


def _read_databus_from_droneengage_configs() -> tuple[str | None, int | None]:
    """Best-effort parse of common DroneEngage config locations."""
    candidate_paths = [
        Path("/etc/droneengage/config.yaml"),
        Path("/etc/droneengage/config.yml"),
        Path("/etc/droneengage/config.json"),
        Path("/opt/droneengage/config.yaml"),
        Path("/opt/droneengage/config.yml"),
        Path("/opt/droneengage/config.json"),
        Path.home() / ".droneengage" / "config.yaml",
        Path.home() / ".droneengage" / "config.yml",
        Path.home() / ".droneengage" / "config.json",
    ]

    def search(value):
        if isinstance(value, dict):
            host = None
            port = None
            for k, v in value.items():
                key = str(k).lower()
                if key in {"databus_host", "databushost"}:
                    host = v
                elif key in {"databus_port", "databusport"}:
                    port = v
            if port is not None:
                return host, port

            for v in value.values():
                nested = search(v)
                if nested is not None:
                    return nested
        elif isinstance(value, list):
            for item in value:
                nested = search(item)
                if nested is not None:
                    return nested
        return None

    for path in candidate_paths:
        if not path.exists() or not path.is_file():
            continue

        suffix = path.suffix.lower()
        try:
            with open(path, "r", encoding="utf-8") as f:
                if suffix == ".json":
                    parsed = json.load(f)
                elif suffix in {".yaml", ".yml"}:
                    parsed = yaml.safe_load(f)
                else:
                    continue
        except (OSError, json.JSONDecodeError, yaml.YAMLError):
            continue

        discovered = search(parsed)
        if discovered is None:
            continue

        host, port = discovered
        try:
            port_int = int(port)
        except (TypeError, ValueError):
            continue

        host_str = str(host) if host else None
        return host_str, port_int

    return None, None


def probe_databus_port(args, cfg) -> tuple[str, int] | None:
    ports = _candidate_ports(args, cfg)
    hosts = _candidate_hosts(args, cfg)
    if not ports or not hosts:
        return None

    probe = json.dumps(
        {"probe": "wingxtra_databus_port_check"}, separators=(",", ":")
    ).encode("utf-8")

    for host in hosts:
        for port in ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(0.08)
            try:
                sock.sendto(probe, (str(host), int(port)))
                _payload, sender = sock.recvfrom(4096)
                if sender[0] == str(host) and sender[1] == int(port):
                    return str(host), int(port)
            except OSError:
                continue
            finally:
                sock.close()

    return None


def discover_databus_endpoint(args, cfg, *, allow_probe: bool) -> tuple[str, int] | None:
    cfg_host, cfg_port = _read_databus_from_droneengage_configs()
    if cfg_port is not None:
        resolved_host = cfg_host or next(iter(_candidate_hosts(args, cfg)), None)
        if resolved_host:
            return str(resolved_host), int(cfg_port)

    if allow_probe:
        return probe_databus_port(args, cfg)

    return None


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
    stability = cfg.get("stability", {})
    max_reproj_rmse_px = float(stability.get("max_reproj_rmse_px", 8.0))
    ema_alpha = float(stability.get("ema_alpha", 0.4))
    stale_timeout_ms = int(stability.get("stale_timeout_ms", 1000))

    last = 0.0
    last_debug_save = 0.0
    last_seen_ts = 0.0
    ema_body: np.ndarray | None = None
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

        if res:
            last_seen_ts = now

        gating_reason = ""
        if res and (now - last) >= period:
            reproj = float(res.get("reproj_rmse_px", 0.0))
            if reproj > max_reproj_rmse_px:
                gating_reason = f"reproj={reproj:.2f}px > {max_reproj_rmse_px:.2f}px"
                res = None

        if res and (now - last) >= period:
            tvec_cam = res["tvec"]
            body = camera_to_body_ned_default(tvec_cam)
            body = (R_extra @ body.reshape(3, 1)).reshape(3)

            if ema_body is None:
                ema_body = body
            else:
                ema_body = ema_alpha * body + (1.0 - ema_alpha) * ema_body

            body_out = ema_body

            pkt = build_landing_target_packet(
                sysid=SYSID,
                compid=COMPID,
                target_num=target_num,
                x_m=float(body_out[0]),
                y_m=float(body_out[1]),
                z_m=float(body_out[2]),
                angle_x=float(res["angle_x"]),
                angle_y=float(res["angle_y"]),
            )

            print(
                "used_ids=%s markers=%d x=%.3f y=%.3f z=%.3f"
                % (
                    res["used_ids"],
                    res["num_markers_used"],
                    float(body_out[0]),
                    float(body_out[1]),
                    float(body_out[2]),
                )
            )

            # Forward to DroneEngage (single FC link)
            if not args.dry_run:
                out.send_landing_target(pkt)

            last = now

        if (now - last_seen_ts) * 1000.0 > stale_timeout_ms:
            ema_body = None

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
                    f"reproj_rmse_px: {float(res.get('reproj_rmse_px', 0.0)):.2f}",
                ]
            else:
                lines = [
                    "used_ids: []",
                    "num_markers_used: 0",
                    "x: n/a",
                    "y: n/a",
                    "z: n/a",
                ]
                if gating_reason:
                    lines.append(f"gate: {gating_reason}")

            stale_ms = max(0.0, (now - last_seen_ts) * 1000.0)
            lines.append(f"stale_ms: {stale_ms:.0f}/{stale_timeout_ms}")

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
