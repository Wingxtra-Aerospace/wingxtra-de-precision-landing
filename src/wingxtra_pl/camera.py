"""Continuously drain the source into a single latest-frame slot.

Network timestamps measure local decode receipt, not exposure time. Transport latency
must be measured on the installed camera. No prerecorded-file source is accepted.
"""

from __future__ import annotations

from dataclasses import dataclass
import threading
import time

import cv2
import numpy as np

from .config import CameraConfig


@dataclass(frozen=True)
class Frame:
    image: np.ndarray
    sequence: int
    monotonic: float
    unix_us: int


class Camera:
    def __init__(self, config: CameraConfig):
        self.config = config
        self.latest = None
        self.error = "Camera is starting"
        self.shutdown_error = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        self.thread = threading.Thread(target=self._run, name="camera", daemon=True)

    def start(self):
        self.thread.start()

    def snapshot(self):
        with self.lock:
            return self.latest

    def _run(self):
        sequence = 0
        while not self.stop_event.is_set():
            capture, picam = None, None
            try:
                c = self.config
                if c.kind == "picamera2":
                    from picamera2 import Picamera2  # Optional, never imported on other systems.

                    picam = Picamera2(int(c.source))
                    picam.configure(
                        picam.create_video_configuration(
                            main={"format": "RGB888", "size": (c.width, c.height)},
                            controls={"FrameRate": c.fps},
                            buffer_count=2,
                            queue=False,
                        )
                    )
                    # Picamera2 RGB888 is byte-ordered BGR, as required by OpenCV.
                    picam.start()
                elif c.kind == "v4l2":
                    capture = cv2.VideoCapture(c.source, cv2.CAP_V4L2)
                    capture.set(cv2.CAP_PROP_FRAME_WIDTH, c.width)
                    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, c.height)
                    capture.set(cv2.CAP_PROP_FPS, c.fps)
                    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                else:
                    capture = cv2.VideoCapture(
                        c.source,
                        cv2.CAP_FFMPEG,
                        [
                            cv2.CAP_PROP_OPEN_TIMEOUT_MSEC,
                            3000,
                            cv2.CAP_PROP_READ_TIMEOUT_MSEC,
                            1000,
                        ],
                    )
                if capture is not None and not capture.isOpened():
                    raise RuntimeError(
                        "Camera could not be opened; check source and device permissions"
                    )
                while not self.stop_event.is_set():
                    if picam is not None:
                        frame = picam.capture_array()
                        ok = frame is not None
                    else:
                        ok, frame = capture.read()
                    received = time.monotonic()
                    if not ok or frame is None:
                        raise RuntimeError("Camera stopped delivering frames")
                    if frame.shape[:2] != (c.height, c.width):
                        raise RuntimeError(
                            f"Camera delivers {frame.shape[1]}×{frame.shape[0]}; "
                            f"configured {c.width}×{c.height}. Frames rejected."
                        )
                    sequence += 1
                    with self.lock:
                        if self.stop_event.is_set():
                            break
                        self.latest = Frame(frame, sequence, received, time.time_ns() // 1000)
                        self.error = None
            except Exception as exc:
                # OpenCV exceptions may include the source URL (and credentials).
                self.error = (
                    str(exc)
                    if isinstance(exc, RuntimeError)
                    else f"Camera failure ({type(exc).__name__}); check setup"
                )
                with self.lock:
                    self.latest = None
            finally:
                with self.lock:
                    self.latest = None
                try:
                    if capture is not None:
                        capture.release()
                    if picam is not None:
                        picam.close()
                except Exception:
                    self.shutdown_error = "Camera driver cleanup failed; restart the extension"
                    self.error = self.shutdown_error
                    self.stop_event.set()
            self.stop_event.wait(1)

    def close(self):
        self.stop_event.set()
        with self.lock:
            self.latest = None
        if self.thread.ident is not None:
            self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError(
                "Camera driver did not stop; restart the extension before reopening it"
            )
        if self.shutdown_error:
            raise RuntimeError(self.shutdown_error)
