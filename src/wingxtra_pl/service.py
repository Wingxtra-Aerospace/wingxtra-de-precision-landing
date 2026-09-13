from __future__ import annotations

from collections import deque
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import threading
import time

import cv2
import numpy as np

from . import __version__
from .calibration import Calibration, CalibrationSession
from .camera import Camera
from .config import Config
from .landing_target_layout import LandingTargetLayout
from .mavlink_out.databus_internal_mavlink import DroneEngageDatabusInternalMavlinkOut
from .mavlink_out.udp import LandingTargetEncoder, RouterLink
from .storage import atomic_json
from .tracking import TargetTracker
from .vision_multitag import DetectorConfig, MultiTagPoseEstimator


class LandingService:
    def __init__(self, data_dir: Path, *, camera_factory=Camera, link_factory=RouterLink):
        self.data = data_dir
        self.data.mkdir(parents=True, exist_ok=True)
        self.camera_factory, self.link_factory = camera_factory, link_factory
        self.lock = threading.RLock()
        self.stop_event = threading.Event()
        self.thread = None
        self.camera = self.link = self.databus = self.estimator = None
        self.calibration = self.session = None
        self.mode = "stopped"
        self.output_inhibited = False
        self.error = None
        self.events = deque(maxlen=100)
        self.log = logging.getLogger(f"wingxtra.{id(self)}")
        self.log.setLevel(logging.INFO)
        self.log.propagate = False
        self.handler = RotatingFileHandler(
            self.data / "measurements.jsonl", maxBytes=10_000_000, backupCount=3
        )
        self.handler.setFormatter(logging.Formatter("%(message)s"))
        self.log.addHandler(self.handler)
        self.config = self._load_config()
        board_path = self.data / "landing-target.json"
        if not board_path.exists():
            default = Path(__file__).parent / "defaults" / "landing-target.json"
            atomic_json(board_path, json.loads(default.read_text()))
        self.board_data = json.loads(board_path.read_text())
        self.layout = LandingTargetLayout.from_dict(self.board_data)
        calibration_path = self.data / "camera.json"
        if calibration_path.exists():
            try:
                self.calibration = Calibration.model_validate_json(calibration_path.read_text())
            except ValueError:
                self.error = "Saved calibration is invalid; recalibrate or import a valid export"
        self.tracker = TargetTracker(self.config.quality)
        self.encoder = LandingTargetEncoder(
            self.config.output.target_system, self.config.output.source_component
        )
        self.last_sequence = -1
        self.last_sent = 0.0
        self.last_tick = time.monotonic()
        self.last_measurement = None
        self.last_preview = None
        self.last_preview_time = 0
        self.sent_count = 0
        self.processed_count = 0
        self.started_time = time.monotonic()
        self._refresh_estimator()

    def _load_config(self):
        path = self.data / "config.json"
        if path.exists():
            return Config.model_validate_json(path.read_text())
        config = Config()
        atomic_json(path, config.model_dump())
        return config

    def event(self, kind: str, **fields):
        record = {"time_unix_us": time.time_ns() // 1000, "event": kind, **fields}
        self.events.append(record)
        self.log.info(json.dumps(record, allow_nan=False, separators=(",", ":")))

    def _refresh_estimator(self):
        self.estimator = None
        if self.calibration and self.calibration.matches(self.config.camera):
            q = self.config.quality
            self.estimator = MultiTagPoseEstimator(
                DetectorConfig(
                    min_tag_edge_px=q.min_tag_edge_px, max_reprojection_px=q.max_reprojection_px
                ),
                self.layout,
                np.array(self.calibration.camera_matrix),
                np.array(self.calibration.distortion_coefficients),
            )

    def _open_link(self):
        try:
            self.link = self.link_factory(self.config.output)
            if self.config.output.mode == "droneengage_databus":
                c = self.config.output
                self.databus = DroneEngageDatabusInternalMavlinkOut(
                    c.databus_host, c.databus_port, module_key=c.databus_module_key
                )
            self.error = None
        except OSError as exc:
            self.error = (
                f"MAVLink endpoint unavailable ({type(exc).__name__}); check address and port"
            )
            self.event("link_error", reason=self.error)

    def start(self):
        with self.lock:
            self._open_link()
            self.thread = threading.Thread(target=self._run, name="landing-engine", daemon=True)
            self.thread.start()
            if self.config.startup_mode != "stopped":
                # Startup publish can wait for a heartbeat, but never bypass calibration.
                try:
                    self.control(self.config.startup_mode)
                except ValueError as exc:
                    self.error = str(exc)
                    self.event("startup_blocked", reason=self.error)

    def assert_editable(self):
        if self.mode == "publish":
            raise ValueError("Stop MAVLink output before changing setup")
        # Preserve last armed state even after heartbeat loss.
        if self.link is not None and self.link.armed is True:
            raise ValueError("Setup is locked while the flight controller is armed")

    def _close_camera(self):
        if self.camera:
            self.camera.close()
            self.camera = None
        self.last_preview = None
        self.last_measurement = None
        self.last_sequence = -1
        self.tracker.reset()

    def control(self, mode: str):
        with self.lock:
            if mode not in {"stopped", "monitor", "publish"}:
                raise ValueError("Unknown operating mode")
            if mode == "publish":
                if self.output_inhibited:
                    raise ValueError("MAVLink output is disabled by --dry-run for this process")
                if self.session is not None:
                    raise ValueError("Finish or cancel the calibration session first")
                if self.estimator is None:
                    raise ValueError("A valid calibration matching this camera is required")
                if self.link is None:
                    raise ValueError("MAVLink endpoint is unavailable; check connection setup")
            self.mode = mode  # Stops output before any potentially slow driver shutdown.
            self.tracker.reset()
            self.last_measurement = None
            if mode == "stopped":
                self.session = None
                self._close_camera()
            elif self.camera is None:
                self.camera = self.camera_factory(self.config.camera)
                self.camera.start()
            self.event("mode", mode=mode)
            return self.status()

    def update_config(self, config: Config):
        with self.lock:
            self.assert_editable()
            self.mode = "stopped"
            self._close_camera()
            self.session = None
            if self.link:
                self.link.close()
                self.link = None
            if self.databus:
                self.databus.close()
                self.databus = None
            atomic_json(self.data / "config.json", config.model_dump())
            self.config = config
            self.tracker = TargetTracker(config.quality)
            self.encoder = LandingTargetEncoder(
                config.output.target_system, config.output.source_component
            )
            self._refresh_estimator()
            self._open_link()
            self.event("configuration_saved")
            return config.model_dump()

    def update_board(self, data):
        layout = LandingTargetLayout.from_dict(data)
        with self.lock:
            self.assert_editable()
            atomic_json(self.data / "landing-target.json", data)
            self.board_data, self.layout = data, layout
            self.tracker.reset()
            self._refresh_estimator()
            self.event("board_saved", tags=list(layout.markers))

    def calibration_start(self, columns=9, rows=6, square_m=0.0245):
        with self.lock:
            self.assert_editable()
            self.control("monitor")
            self.session = CalibrationSession(self.config.camera, columns, rows, square_m)
            return self.session.status()

    def calibration_capture(self):
        with self.lock:
            self.assert_editable()
            if self.session is None or self.camera is None:
                raise ValueError("Start a calibration session first")
            frame = self.camera.snapshot()
            if frame is None or time.monotonic() - frame.monotonic > 0.5:
                raise ValueError("No fresh camera frame available")
            return self.session.capture(frame.image, frame.sequence)

    def calibration_solve(self):
        with self.lock:
            self.assert_editable()
            if self.session is None:
                raise ValueError("No calibration session")
            calibration = self.session.solve()
            self.import_calibration(calibration)
            self.session = None
            return calibration.model_dump()

    def import_calibration(self, calibration: Calibration):
        with self.lock:
            self.assert_editable()
            if not calibration.matches(self.config.camera):
                raise ValueError("Calibration source, lens profile or resolution does not match")
            atomic_json(self.data / "camera.json", calibration.model_dump())
            self.calibration = calibration
            self.session = None
            self._refresh_estimator()
            self.tracker.reset()
            self.event("calibration_saved", rms_px=calibration.rms_px, views=calibration.views)

    def _run(self):
        while not self.stop_event.wait(0.005):
            with self.lock:
                try:
                    self.tick()
                except Exception as exc:
                    self.tracker.reject("Processing failure")
                    self.error = f"Processing failure ({type(exc).__name__}); output stopped"
                    self.mode = "monitor" if self.camera else "stopped"
                    self.event("processing_error", reason=self.error)

    def tick(self):
        now = time.monotonic()
        self.last_tick = now
        if self.link:
            self.link.poll(now)
        if self.mode == "stopped" or self.camera is None:
            return
        frame = self.camera.snapshot()
        if frame is None or now - frame.monotonic > self.config.quality.max_frame_age_s:
            self.tracker.reject(self.camera.error or "Camera frame too old")
            return
        if frame.sequence == self.last_sequence:
            return
        self.last_sequence = frame.sequence
        pose = self.estimator.estimate(frame.image) if self.estimator else None
        self.processed_count += 1
        body = np.asarray(self.config.mount.camera_to_body) @ pose["tvec"] if pose else None
        now = time.monotonic()
        accepted = self.tracker.accept(pose, body, frame.monotonic, now, frame.sequence)
        if self.estimator is None:
            self.tracker.reject("Calibrate this camera to estimate a target")
        reason = self.tracker.reason
        sent = False
        if accepted and self.mode == "publish":
            if not self.link or not self.link.fresh(now):
                reason = "Waiting for flight-controller heartbeat"
            elif now - self.last_sent >= 1 / self.config.output.send_hz:
                packet = self.encoder.encode(body, frame.unix_us, self.layout.target_num)
                if self.databus:
                    self.databus.send_landing_target(packet)
                    sent = True
                else:
                    sent = self.link.send(packet, now)
                if sent:
                    self.last_sent = now
                    self.sent_count += 1
        self.last_measurement = {
            "sequence": frame.sequence,
            "capture_unix_us": frame.unix_us,
            "processed_monotonic": now,
            "age_ms": round((now - frame.monotonic) * 1000, 1),
            "accepted": accepted,
            "sent": sent,
            "reason": reason,
            "body_frd_m": body.tolist() if body is not None else None,
            "distance_m": float(np.linalg.norm(body)) if body is not None else None,
            "used_ids": pose["used_ids"] if pose else [],
            "reprojection_px": pose["reproj_rmse_px"] if pose else None,
        }
        self.event("measurement", **self.last_measurement)
        if now - self.last_preview_time >= 0.2:
            preview = frame.image.copy()
            if pose:
                for corners, mid in zip(pose["image_corners"], pose["used_ids"]):
                    points = np.round(corners).astype(np.int32)
                    cv2.polylines(preview, [points], True, (180, 220, 50), 2)
                    cv2.putText(
                        preview,
                        str(mid),
                        tuple(points[0]),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (180, 220, 50),
                        2,
                    )
                origin = cv2.projectPoints(
                    np.zeros((1, 3)),
                    pose["rvec"],
                    pose["tvec"],
                    self.estimator.K,
                    self.estimator.dist,
                )[0].reshape(2)
                if np.isfinite(origin).all() and np.max(np.abs(origin)) < 100000:
                    cv2.drawMarker(
                        preview, tuple(origin.astype(int)), (0, 190, 255), cv2.MARKER_CROSS, 24, 2
                    )
            scale = min(1, 960 / preview.shape[1])
            if scale < 1:
                preview = cv2.resize(preview, None, fx=scale, fy=scale)
            ok, encoded = cv2.imencode(".jpg", preview, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if ok:
                self.last_preview = encoded.tobytes()
                self.last_preview_time = now

    def status(self):
        with self.lock:
            now = time.monotonic()
            frame = self.camera.snapshot() if self.camera else None
            measurement = dict(self.last_measurement) if self.last_measurement else None
            if measurement:
                measurement["current_age_ms"] = round(
                    (now - measurement["processed_monotonic"]) * 1000 + measurement["age_ms"], 1
                )
                if measurement["current_age_ms"] > self.config.quality.max_frame_age_s * 1000:
                    measurement.update(accepted=False, sent=False, reason="Measurement is stale")
            return {
                "version": __version__,
                "mode": self.mode,
                "dry_run": self.output_inhibited,
                "error": self.error,
                "engine_alive": self.thread is not None
                and self.thread.is_alive()
                and now - self.last_tick < 5,
                "camera": {
                    "connected": frame is not None and now - frame.monotonic < 0.5,
                    "error": self.camera.error if self.camera else None,
                    "width": self.config.camera.width,
                    "height": self.config.camera.height,
                    "age_ms": round((now - frame.monotonic) * 1000, 1) if frame else None,
                },
                "connection": self.link.status(now)
                if self.link
                else {"connected": False, "armed": None, "heartbeat_age_s": None},
                "calibration": {
                    "valid": self.estimator is not None,
                    "rms_px": self.calibration.rms_px if self.calibration else None,
                    "views": self.calibration.views if self.calibration else 0,
                    "session": self.session.status() if self.session else None,
                },
                "board": {"tags": len(self.layout.markers), "ids": list(self.layout.markers)},
                "measurement": measurement,
                "tracking_reason": self.tracker.reason,
                "sent_count": self.sent_count,
                "processed_count": self.processed_count,
                "uptime_s": round(now - self.started_time, 1),
                "events": list(self.events)[-15:],
            }

    def close(self):
        self.stop_event.set()
        with self.lock:
            self.mode = "stopped"
            self._close_camera()
            if self.link:
                self.link.close()
            if self.databus:
                self.databus.close()
        if self.thread:
            self.thread.join(timeout=5)
        self.handler.close()
        self.log.removeHandler(self.handler)
