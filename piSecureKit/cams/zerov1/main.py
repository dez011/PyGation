#!/usr/bin/env python3
"""
PiSecureKit - Raspberry Pi Camera Security System (OOP + type-safe refactor)
"""
from __future__ import annotations

import os
import time
import signal
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Optional, runtime_checkable

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOG = logging.getLogger("PiSecureKit")

# ---------- Optional camera imports ----------
CAMERA_AVAILABLE = True
try:
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, Quality
    from picamera2.outputs import FfmpegOutput
except Exception as _exc:  # pragma: no cover (dev machines)
    LOG.warning("Camera modules not available: %s", _exc)
    CAMERA_AVAILABLE = False


# ---------- Configuration ----------
@dataclass(frozen=True)
class RtspConfig:
    host: str                # e.g., "192.168.6.76"
    port: int = 8554
    path: str = "hqstream"
    tcp: bool = True

    def url(self) -> str:
        # rtsp://HOST:PORT/PATH
        return f"rtsp://{self.host}:{self.port}/{self.path}"

    def ffmpeg_flags(self) -> str:
        # Keep it explicit & easy to tweak
        base = "-f rtsp"
        if self.tcp:
            base += " -rtsp_transport tcp"
        # copy the encoded video stream, drop audio
        return f"-c:v copy -an {base}"


@dataclass(frozen=True)
class VideoConfig:
    # Picamera2 main and lores stream sizes & formats
    width: int = 1640
    height: int = 1232
    format: str = "YUV420"
    frame_rate: int = 30
    bitrate: int = 4_000_000
    iperiod: int = 30  # keyframe interval
    lores_enabled: bool = False
    lores_width: int = 640
    lores_height: int = 480


@dataclass(frozen=True)
class AppConfig:
    rtsp: RtspConfig
    video: VideoConfig = VideoConfig()
    preview_jpeg_path: Path = Path("/dev/shm/camera-tmp.jpg")
    preview_interval_sec: float = 5.0


# ---------- Camera Abstraction ----------
@runtime_checkable
class CameraDriver(Protocol):
    """Protocol for concrete camera drivers (real or mock)."""

    def start(self) -> None: ...
    def stop(self) -> None: ...
    def capture_still(self, destination: Path) -> None: ...


class NullCamera(CameraDriver):
    """Dev-machine fallback that simulates work without hardware."""
    def __init__(self, fps: int = 30) -> None:
        self._running = False
        self._fps = fps

    def start(self) -> None:
        LOG.info("[NullCamera] start (simulating %s FPS stream)", self._fps)
        self._running = True

    def stop(self) -> None:
        if self._running:
            LOG.info("[NullCamera] stop")
            self._running = False

    def capture_still(self, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        # Write a tiny placeholder file
        destination.write_bytes(b"\xFF\xD8\xFF\xD9")  # minimal JPEG SOI/EOI
        LOG.debug("[NullCamera] wrote placeholder still to %s", destination)


class Picamera2Driver(CameraDriver):
    """Real Picamera2-backed implementation."""
    def __init__(self, cfg: AppConfig) -> None:
        if not CAMERA_AVAILABLE:
            raise RuntimeError("Picamera2 not available on this system.")
        self._cfg = cfg
        self._picam2 = Picamera2()
        self._encoder = H264Encoder(
            bitrate=self._cfg.video.bitrate,
            repeat=True,
            iperiod=self._cfg.video.iperiod
        )
        self._output = FfmpegOutput(
            f"{self._cfg.rtsp.ffmpeg_flags()} {self._cfg.rtsp.url()}",
            audio=False
        )
        self._started = False

        # Attempt a series of increasingly lighter configurations to avoid DMA/CMA OOM
        attempts = [
            # (width, height, pixel_format, buffer_count, use_lores)
            (self._cfg.video.width, self._cfg.video.height, self._cfg.video.format, 3, self._cfg.video.lores_enabled),
            (1280, 720,       "YUV420", 3, False),
            (1280, 720,       "YUV420", 2, False),
            (1024, 576,       "YUV420", 2, False),
            (640,  480,       "YUV420", 2, False),
        ]

        configured = False
        for (w, h, fmt, buffers, use_lores) in attempts:
            if self._try_configure(w, h, fmt, buffers, use_lores):
                LOG.info("Configured camera: %dx%d %s (buffers=%d, lores=%s)", w, h, fmt, buffers, use_lores)
                configured = True
                break

        if not configured:
            raise RuntimeError("Failed to configure Picamera2 after multiple attempts; likely CMA/DMA memory is insufficient.")

    def _try_configure(self, main_w: int, main_h: int, main_fmt: str, buffer_count: int, use_lores: bool) -> bool:
        try:
            kwargs = {
                "main": {"size": (main_w, main_h), "format": main_fmt},
                "controls": {"FrameRate": self._cfg.video.frame_rate},
            }
            if use_lores:
                kwargs["lores"] = {"size": (self._cfg.video.lores_width, self._cfg.video.lores_height), "format": "YUV420"}
            video_conf = self._picam2.create_video_configuration(**kwargs)
            video_conf["buffer_count"] = buffer_count
            self._picam2.align_configuration(video_conf)
            self._picam2.configure(video_conf)
            return True
        except Exception as e:
            LOG.warning("Configure attempt failed for %dx%d %s (buffers=%d, lores=%s): %s", main_w, main_h, main_fmt, buffer_count, use_lores, e)
            return False

    def start(self) -> None:
        if self._started:
            return
        LOG.info("Starting Picamera2 RTSP to %s", self._cfg.rtsp.url())
        # Quality.LOW here reduces encoder load for stability; adjust if desired
        self._picam2.start_recording(self._encoder, self._output, quality=Quality.LOW)
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        LOG.info("Stopping Picamera2")
        try:
            self._picam2.stop_recording()
        finally:
            self._started = False

    def capture_still(self, destination: Path) -> None:
        req = self._picam2.capture_request()
        try:
            req.save("main", str(destination))
        finally:
            req.release()


# ---------- Orchestration ----------
class StreamService:
    """
    Owns a CameraDriver lifecycle and optional periodic preview capture.
    Use as a context manager for guaranteed cleanup.
    """
    def __init__(self, camera: CameraDriver, cfg: AppConfig) -> None:
        self._camera = camera
        self._cfg = cfg
        self._running = False

    def __enter__(self) -> "StreamService":
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

    def start(self) -> None:
        if self._running:
            return
        self._camera.start()
        self._running = True

    def stop(self) -> None:
        if not self._running:
            return
        self._camera.stop()
        self._running = False

    def run_forever(self) -> None:
        """
        Blocks; periodically captures a still for preview.
        Use SIGINT/SIGTERM to stop.
        """
        LOG.info("StreamService running; preview every %.1fs -> %s",
                 self._cfg.preview_interval_sec, self._cfg.preview_jpeg_path)

        next_tick = time.monotonic()
        try:
            while self._running:
                now = time.monotonic()
                if now >= next_tick:
                    try:
                        self._camera.capture_still(self._cfg.preview_jpeg_path)
                    except Exception as e:
                        LOG.exception("Still capture failed: %s", e)
                    next_tick = now + self._cfg.preview_interval_sec
                time.sleep(0.05)  # small sleep to avoid tight loop
        finally:
            LOG.info("StreamService loop exiting")


# ---------- Wiring / Bootstrap ----------
def build_camera(cfg: AppConfig) -> CameraDriver:
    if CAMERA_AVAILABLE:
        return Picamera2Driver(cfg)
    LOG.warning("Using NullCamera (no hardware).")
    return NullCamera(fps=cfg.video.frame_rate)


def install_signal_handlers(stop_cb) -> None:
    def _handler(signum, _frame):
        LOG.info("Received signal %s, shutting down...", signum)
        stop_cb()

    for s in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(s, _handler)
        except Exception:
            # Not all platforms allow setting these (e.g., certain threads)
            pass


def main() -> int:
    # Read host from env or default to your original
    hub_host = os.getenv("PISECUREKIT_HUB", "192.168.4.19")

    cfg = AppConfig(
        rtsp=RtspConfig(host=hub_host, port=8554, path="hqstream"),
        video=VideoConfig(
            width=1640, height=1232, format="YUV420",
            frame_rate=30, bitrate=4_000_000, iperiod=30,
            lores_enabled=False,
            lores_width=640,
            lores_height=480,
        ),
        preview_jpeg_path=Path("/dev/shm/camera-tmp.jpg"),
        preview_interval_sec=5.0
    )

    camera = build_camera(cfg)
    service = StreamService(camera, cfg)

    # graceful shutdown
    install_signal_handlers(service.stop)

    LOG.info("Starting camera streams…")
    with service:
        # block here until signal or exception
        service.run_forever()
    LOG.info("Camera streams stopped.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as e:
        LOG.exception("Fatal error: %s", e)
        raise