from __future__ import annotations

import time
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
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    K = np.array(data["camera_matrix"]["data"], dtype=float).reshape(3, 3)
    dist = np.array(data["distortion_coefficients"]["data"], dtype=float).reshape(-1, 1)
    return K, dist


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
        distance=0.0,     # not used when position_valid=1
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


def main():
    cfg = yaml.safe_load(open("config.yaml", "r", encoding="utf-8"))

    layout = LandingTargetLayout.from_landmark_json(cfg["landing_target"]["layout_json"])
    # sanity: your file says tag36h11 and multiple ids, plus target_num. :contentReference[oaicite:4]{index=4}
    target_num = int(cfg["landing_target"].get("target_num", layout.target_num))

    K, dist = load_camera_yaml("camera.yaml")

    estimator = MultiTagPoseEstimator(
        DetectorConfig(opencv_dictionary=cfg["landing_target"]["opencv_dictionary"]),
        layout,
        K,
        dist,
    )

    out = DroneEngageDatabusInternalMavlinkOut(
        host=str(cfg["mavlink_out"]["databus_host"]),
        port=int(cfg["mavlink_out"]["databus_port"]),
    )

    send_hz = float(cfg["mavlink"]["send_hz"])
    period = 1.0 / max(send_hz, 1.0)
    last = 0.0

    rpy = cfg["frames"]["cam_to_body_rpy_deg"]
    R_extra = rpy_deg_to_rotmat(float(rpy[0]), float(rpy[1]), float(rpy[2]))

    # Camera setup (IMX219 via libcamera / Picamera2)
    picam2 = Picamera2()
    w = int(cfg["camera"]["width"])
    h = int(cfg["camera"]["height"])
    video_config = picam2.create_video_configuration(main={"format": "RGB888", "size": (w, h)})
    picam2.configure(video_config)
    picam2.start()

    # MAVLink identity for the companion/plugin
    SYSID = 42
    COMPID = 191

    while True:
        frame_rgb = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

        res = estimator.estimate(frame_bgr)
        now = time.time()

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

            # Forward to DroneEngage (single FC link)
            out.send_landing_target(pkt)

            last = now

        time.sleep(0.001)


if __name__ == "__main__":
    main()
