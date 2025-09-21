#!/usr/bin/env python3
"""
PiSecureKit - Raspberry Pi Camera Security System
"""

# Standard library imports
import io
import os
import time
import logging
# import subprocess
# import threading
# import atexit
# from datetime import datetime
# from threading import Condition

# Third-party imports
# from flask import Flask, render_template, Response
# from flask_restful import Resource, Api

# Camera-specific imports
try:
    import picamera2
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, MJPEGEncoder, Quality
    from picamera2.outputs import FileOutput, CircularOutput, FfmpegOutput
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
video_config = picam2.create_video_configuration(main={"size": (1640, 1232), "format": "RGB888"},
                                                 lores={"size": (640, 480), "format": "YUV420"},
                                                 controls={'FrameRate': frame_rate})
picam2.align_configuration(video_config)
picam2.configure(video_config)

HQoutput = FfmpegOutput(f"-c:v copy -an -f rtsp -rtsp_transport tcp rtsp://{HUB}:8554/hqstream", audio=False)
# LQoutput = FfmpegOutput("-f rtsp -rtsp_transport tcp rtsp://192.168.6.76:8554/lqstream", audio=False)

# Encoder settings
encoder_HQ = H264Encoder(bitrate=4_000_000, repeat=True, iperiod=30)
# encoder_LQ = H264Encoder(repeat=True, iperiod=30, framerate=frame_rate, enable_sps_framerate=True)

try:
    print("trying to start camera streams")
    picam2.start_recording(encoder_HQ, HQoutput, quality=Quality.LOW)
    # picam2.start_recording(encoder_LQ, LQoutput, quality=Quality.LOW, name="lores")
    print("Started camera streams")
    while True:
        time.sleep(5)
        still = picam2.capture_request()
        still.save("main", "/dev/shm/camera-tmp.jpg")
        still.release()
        # os.rename('/dev/shm/camera-tmp.jpg', '/dev/shm/camera.jpg') # make image replacement atomic operation
except Exception as e:
    print("exiting picamera2 streamer due to exception:", e)
    picam2.stop_recording()
