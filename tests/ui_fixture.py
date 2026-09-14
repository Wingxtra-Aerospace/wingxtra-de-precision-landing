"""Browser-test fixture only: synthetic image, known intrinsics, output hard-inhibited."""

from contextlib import asynccontextmanager
from pathlib import Path
import tempfile
import time

import cv2
from fastapi import FastAPI
import numpy as np
import uvicorn

from wingxtra_pl.calibration import Calibration
from wingxtra_pl.camera import Frame
from wingxtra_pl.config import Config
from wingxtra_pl.service import LandingService
from wingxtra_pl.storage import atomic_json
from wingxtra_pl.web import create_app
from conftest import render_board
from test_protocol_tracking import free_port

cv2.setNumThreads(2)
data = Path(tempfile.mkdtemp(prefix="wingxtra-ui-test-"))
config = Config()
config.output.listen_port = free_port()
atomic_json(data / "config.json", config.model_dump())
k = np.array([[850.0, 0, 640], [0, 850, 360], [0, 0, 1]])


class SyntheticCamera:
    error = None

    def __init__(self, config):
        self.started = time.monotonic()

    def start(self):
        pass

    def snapshot(self):
        seq = int((time.monotonic() - self.started) * 30)
        return Frame(image, seq, self.started + seq / 30, time.time_ns() // 1000)

    def close(self):
        pass


service = LandingService(data, camera_factory=SyntheticCamera)
service.output_inhibited = True
image = render_board(service.layout, k, r=[np.pi - 0.08, 0.03, 0.02], t=[0, 0, 0.9])
cv2.putText(
    image,
    "SYNTHETIC TEST IMAGE - MAVLINK OUTPUT DISABLED",
    (25, 45),
    cv2.FONT_HERSHEY_SIMPLEX,
    0.65,
    (20, 20, 160),
    2,
)
service.import_calibration(
    Calibration(
        camera_fingerprint=config.camera.fingerprint(),
        image_width=1280,
        image_height=720,
        camera_matrix=k.tolist(),
        distortion_coefficients=[0] * 5,
        rms_px=0,
        per_view_rms_px=[0] * 15,
        views=15,
        created_utc="synthetic-browser-test-fixture",
    )
)


@asynccontextmanager
async def lifespan(app):
    service.start()
    try:
        yield
    finally:
        service.close()


app = FastAPI(lifespan=lifespan)
app.mount("/extensionv2/wingxtraprecisionlanding", create_app(data, service))
uvicorn.run(app, host="127.0.0.1", port=18077, access_log=False)
