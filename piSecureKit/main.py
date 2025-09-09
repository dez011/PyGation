#!/usr/bin/env python3
"""
PiSecureKit - Raspberry Pi Camera Security System
"""

# Standard library imports
import io
import logging
from threading import Condition

# Third-party imports
from flask import Flask, Response
from flask_restful import Resource, Api

from Camera import Camera
from utils import gen_frames

# Camera-specific imports
try:
    import picamera2
    from picamera2 import Picamera2
    from picamera2.encoders import H264Encoder, MJPEGEncoder
    from picamera2.outputs import FileOutput, CircularOutput, FfmpegOutput
    from libcamera import Transform
    CAMERA_AVAILABLE = True
except ImportError:
    logging.warning("Camera modules not available. Camera functionality will be disabled.")
    CAMERA_AVAILABLE = False

# ========================= Configuration =========================
CONFIG = {
    'DEBUG': False,
    'HOST': '0.0.0.0',
    'PORT': 5000,
    'VIDEO_SIZE': (800, 600),
    'ENCODER_BITRATE': 10000000,  # 10 Mbps
    'PICTURE_DIR': '/home/allzero22/Webserver/webcam/static/pictures/',
    'VIDEO_DIR': '/home/allzero22/Webserver/webcam/static/video/',
    'SOUND_DIR': '/home/allzero22/Webserver/webcam/static/sound/'
}
stream_name = "fd"  # change to your deviceId
rtsp_url = f"rtsp://pi5.local:8554/{stream_name}"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================= Streaming Output Class =========================
class StreamingOutput(io.BufferedIOBase):
    """Buffer for camera output streaming"""

    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        """Write a new frame to the buffer"""
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

# ========================= Camera Handler Class =========================

# ========================= Frame Generator =========================

# ========================= Helper Functions =========================

# ========================= Flask App Setup =========================
app = Flask(__name__, template_folder='template', static_url_path='/static')
api = Api(app)

# Initialize camera
camera = Camera() if CAMERA_AVAILABLE else None

# Register cleanup handler

# ========================= Flask Routes =========================


# ========================= API Resources =========================
class VideoFeed(Resource):
    def get(self):
        """API endpoint for video feed"""
        if not camera:
            return "Camera not available", 500
        return Response(
            gen_frames(camera),
            mimetype='multipart/x-mixed-replace; boundary=frame'
        )

api.add_resource(VideoFeed, '/cam')

# ========================= Main =========================
if __name__ == '__main__':
    logger.info(f"Starting server on {CONFIG['HOST']}:{CONFIG['PORT']}")
    app.run(
        host=CONFIG['HOST'],
        port=CONFIG['PORT'],
        debug=CONFIG['DEBUG'],
        threaded=True
    )