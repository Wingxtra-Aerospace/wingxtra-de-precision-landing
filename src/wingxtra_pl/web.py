from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .board_svg import board_svg
from .calibration import Calibration, chessboard_svg
from .camera_profiles import camera_profiles
from .config import Config, Model
from .service import LandingService


class Control(Model):
    mode: str


class CalibrationSetup(Model):
    columns: int = Field(default=9, ge=3, le=15)
    rows: int = Field(default=6, ge=3, le=15)
    square_m: float = Field(default=0.0245, ge=0.005, le=0.15)


def create_app(data_dir: Path, service=None) -> FastAPI:
    service = service or LandingService(data_dir)

    @asynccontextmanager
    async def lifespan(app):
        service.start()
        try:
            yield
        finally:
            service.close()

    app = FastAPI(
        title="Wingxtra Precision Landing",
        version="1.0.0-rc.2",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
    )
    app.state.service = service
    static = Path(__file__).parent / "static"
    app.mount("/assets", StaticFiles(directory=static), name="assets")

    @app.middleware("http")
    async def protect_mutations(request: Request, call_next):
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            # Custom header plus no CORS prevents cross-site forms / fetch from
            # configuring an aircraft. Access is otherwise the trusted BlueOS LAN.
            if request.headers.get("X-Wingxtra-Request") != "1":
                return JSONResponse(
                    {"detail": "Missing X-Wingxtra-Request header"}, status_code=403
                )
            size = 0
            chunks = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 1_000_000:
                    return JSONResponse({"detail": "Request exceeds 1 MB"}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ValueError)
    async def invalid_value(request, exc):
        return JSONResponse({"detail": str(exc)}, status_code=409)

    @app.get("/")
    def index():
        return FileResponse(static / "index.html")

    @app.get("/register_service")
    def register():
        return {
            "name": "Wingxtra Precision Landing",
            "description": "Calibrated multi-tag landing",
            "icon": "mdi-target",
            "company": "Wingxtra Aerospace Ltd.",
            "version": "1.0.0-rc.2",
            "webpage": "/",
            "api": "/openapi.json",
            "works_in_relative_paths": True,
        }

    @app.get("/health")
    def health():
        healthy = service.status()["engine_alive"]
        return JSONResponse({"alive": healthy}, status_code=200 if healthy else 503)

    @app.get("/api/status")
    def status():
        return service.status()

    @app.get("/api/camera-profiles")
    def profiles_get():
        return camera_profiles()

    @app.get("/api/config")
    def config_get():
        return service.config.model_dump()

    @app.put("/api/config")
    def config_put(config: Config):
        return service.update_config(config)

    @app.post("/api/control")
    def control(command: Control):
        return service.control(command.mode)

    @app.get("/api/preview.jpg")
    def preview():
        with service.lock:
            image = service.last_preview
            if not 0 <= time.monotonic() - service.last_preview_time <= 0.5:
                image = None
        if image is None:
            raise HTTPException(404, "No fresh camera preview available")
        return Response(image, media_type="image/jpeg")

    @app.get("/api/board")
    def board_get():
        return service.board_data

    @app.put("/api/board")
    def board_put(board: dict):
        service.update_board(board)
        return {"tags": len(service.layout.markers)}

    @app.get("/api/board.svg")
    def board_image():
        return Response(
            board_svg(service.layout),
            media_type="image/svg+xml",
            headers={"Content-Disposition": 'inline; filename="landing-board.svg"'},
        )

    @app.get("/api/chessboard.svg")
    def chessboard(columns: int = 9, rows: int = 6, square_mm: float = 24.5):
        return Response(
            chessboard_svg(columns, rows, square_mm),
            media_type="image/svg+xml",
            headers={"Content-Disposition": 'attachment; filename="chessboard.svg"'},
        )

    @app.post("/api/calibration/start")
    def calibration_start(setup: CalibrationSetup):
        return service.calibration_start(**setup.model_dump())

    @app.post("/api/calibration/capture")
    def calibration_capture():
        return service.calibration_capture()

    @app.post("/api/calibration/solve")
    def calibration_solve():
        return service.calibration_solve()

    @app.post("/api/calibration/cancel")
    def calibration_cancel():
        with service.lock:
            service.assert_editable()
            service.session = None
        return {"cancelled": True}

    @app.get("/api/calibration")
    def calibration_get():
        if service.calibration is None:
            raise HTTPException(404, "No saved calibration")
        return JSONResponse(
            service.calibration.model_dump(),
            headers={"Content-Disposition": 'attachment; filename="camera.json"'},
        )

    @app.put("/api/calibration")
    def calibration_put(calibration: Calibration):
        service.import_calibration(calibration)
        return {"saved": True}

    @app.get("/api/logs")
    def logs():
        return FileResponse(
            service.data / "measurements.jsonl",
            filename="measurements.jsonl",
            media_type="application/x-ndjson",
        )

    return app
