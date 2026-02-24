import time
import yaml
import numpy as np
import cv2
from picamera2 import Picamera2

CHESSBOARD = (9, 6)  # inner corners
SQUARE_SIZE_M = 0.0245  # measure your print (meters)
NUM_GOOD_FRAMES = 25
WIDTH, HEIGHT = 1280, 720


def main():
    objp = np.zeros((CHESSBOARD[0] * CHESSBOARD[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0 : CHESSBOARD[0], 0 : CHESSBOARD[1]].T.reshape(-1, 2)
    objp *= SQUARE_SIZE_M

    objpoints, imgpoints = [], []

    picam2 = Picamera2()
    cfg = picam2.create_video_configuration(
        main={"format": "RGB888", "size": (WIDTH, HEIGHT)}
    )
    picam2.configure(cfg)
    picam2.start()

    print("Show chessboard at different angles/distances. Capturing...")
    good = 0
    while good < NUM_GOOD_FRAMES:
        frame_rgb = picam2.capture_array()
        frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        ret, corners = cv2.findChessboardCorners(gray, CHESSBOARD, None)
        if not ret:
            time.sleep(0.05)
            continue

        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001),
        )

        objpoints.append(objp)
        imgpoints.append(corners2)
        good += 1
        print(f"Captured {good}/{NUM_GOOD_FRAMES}")
        time.sleep(0.2)

    ok, mtx, dist, _, _ = cv2.calibrateCamera(
        objpoints, imgpoints, (WIDTH, HEIGHT), None, None
    )
    if not ok:
        raise RuntimeError("Calibration failed")

    out = {
        "image_width": WIDTH,
        "image_height": HEIGHT,
        "camera_matrix": {"rows": 3, "cols": 3, "data": mtx.reshape(-1).tolist()},
        "distortion_coefficients": {
            "rows": int(dist.size),
            "cols": 1,
            "data": dist.reshape(-1).tolist(),
        },
        "distortion_model": "plumb_bob",
    }

    with open("camera.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(out, f, sort_keys=False)

    print("Saved camera.yaml")


if __name__ == "__main__":
    main()
