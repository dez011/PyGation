#!/usr/bin/env python3
"""
PiSecureKit - Raspberry Pi Camera Security System
"""

# Standard library imports
import io
import os
import time
import logging
import subprocess
import threading
import atexit
from datetime import datetime
from threading import Condition

# Third-party imports
# from flask import Flask, render_template, Response
# from flask_restful import Resource, Api

# Camera-specific imports
try:
    import picamera2
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, MJPEGEncoder, Quality
    from picamera2.outputs import FileOutput, CircularOutput, FfmpegOutput, PyavOutput
    from libcamera import Transform
    CAMERA_AVAILABLE = True
except ImportError:
    logging.warning("Camera modules not available. Camera functionality will be disabled.")
    CAMERA_AVAILABLE = False

HUB = "192.168.6.76"        # <-- Pi5 hub IP (not localhost)
USER = "myuser"
PASS = "mypass"


picam2 = Picamera2()
frame_rate = 30
# max resolution is (3280, 2464) for full FoV at 15FPS
video_config = picam2.create_video_configuration(main={"size": (640, 480), "format": "YUV420"},
                                                 lores={"size": (640, 480), "format": "YUV420"},
                                                 controls={'FrameRate': frame_rate}, buffer_count=2)
video_config2 = picam2.create_video_configuration(
    main={"size": (1280, 720), "format": "YUV420"},  # compact, encoder-friendly
    lores=None,         # <- turn OFF extra lores stream
    raw=None,           # <- turn OFF RAW stream (huge CMA hit)
    controls={"FrameRate": 30},
    buffer_count=3      # <- fewer DMA buffers = less CMA
)

picam2.align_configuration(video_config)
picam2.configure(video_config2)
picam2.set_controls({"AfMode": 0})  # 0=Manual; avoids PDAF path on IMX708

# FFMPEG output config
# HQoutput = FfmpegOutput("-f rtsp -rtsp_transport udp rtsp://myuser:mypass@localhost:8554/hqstream", audio=False)
# HQoutput = FfmpegOutput("-f rtsp -rtsp_transport tcp rtsp://192.168.6.76:8554/hqstream", audio=False)
# LQoutput = FfmpegOutput(f"-c:v copy -an -f rtsp -rtsp_transport tcp rtsp://{HUB}:8554/lqstream", audio=False)

#worksv
# HQoutput = FfmpegOutput(f"-c:v copy -an -f rtsp -rtsp_transport tcp rtsp://{HUB}:8554/hqstream", audio=True)
# Fixed HQoutput - removed -c:v copy and fixed audio mismatch

# Prefer PyAV for proper PTS; fall back to FFMPEG if PyAV is unavailable
try:
    HQoutput = PyavOutput(f"rtsp://{HUB}:8554/hqstream", format="rtsp")
    logging.info("Using PyavOutput (rtsp) for accurate timestamps")
except Exception as e:
    logging.warning("PyavOutput not available (%s); falling back to FfmpegOutput", e)
    HQoutput = FfmpegOutput(
        f"-fflags +genpts -use_wallclock_as_timestamps 1 "
        f"-rtsp_transport tcp -muxdelay 0 -muxpreload 0 "
        f"-f rtsp rtsp://{HUB}:8554/hqstream",
        audio=False
    )

# LQoutput = FfmpegOutput(
#     f"-fflags +genpts -use_wallclock_as_timestamps 1 "
#     f"-rtsp_transport tcp -muxdelay 0 -muxpreload 0 "
#     f"-f rtsp rtsp://{HUB}:8554/lqstream",
#     audio=False
# )

# Encoder settings
encoder_HQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)
# encoder_LQ = H264Encoder(repeat=True, iperiod=30, framerate=frame_rate, enable_sps_framerate=True)
# Encoder settings (replace your encoder_LQ line)
encoder_LQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)

retries = 0
MAX_RETRIES = 10
print("starting camera watchdog loop")
while True:
    try:
        print("starting camera streams…")
        picam2.start_recording(encoder_HQ, HQoutput)
        print("camera streams started")
        last_still = 0.0
        while True:
            now = time.monotonic()
            if now - last_still >= 5.0:
                req = picam2.capture_request()
                try:
                    req.save("main", "/dev/shm/camera-tmp.jpg")
                finally:
                    req.release()
                last_still = now
            time.sleep(0.05)
    except Exception as e:
        logging.error("streamer exception: %s", e)
        # Stop recording and attempt reconfigure/restart
        try:
            picam2.stop_recording()
        except Exception:
            pass
        retries += 1
        if retries > MAX_RETRIES:
            logging.critical("too many failures; exiting watchdog")
            break
        # Re-align and re-configure with safer settings in case CMA fragmented
        try:
            safe_conf = picam2.create_video_configuration(
                main={"size": (1280, 720), "format": "YUV420"},
                lores=None,
                raw=None,
                controls={"FrameRate": 30},
                buffer_count=2,
            )
            picam2.align_configuration(safe_conf)
            picam2.configure(safe_conf)
            picam2.set_controls({"AfMode": 0})
        except Exception as reconf_err:
            logging.error("reconfigure failed: %s", reconf_err)
        # Short backoff before retry
        time.sleep(2.0)
        continue
