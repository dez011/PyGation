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
from flask import Flask, render_template, Response
from flask_restful import Resource, Api

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
class Camera:
    """Camera handler for video streaming and image capture"""

    def __init__(self):
        """Initialize camera with default configuration"""
        if not CAMERA_AVAILABLE:
            logger.error("Camera modules not available. Cannot initialize camera.")
            self.camera = None
            return

        try:
            self.camera = Picamera2()
            self.camera.configure(self.camera.create_video_configuration(
                main={"size": CONFIG['VIDEO_SIZE']}
            ))
            self.still_config = self.camera.create_still_configuration()

            # Setup encoder and output for streaming
            self.encoder = MJPEGEncoder(CONFIG['ENCODER_BITRATE'])
            self.streamOut = StreamingOutput()
            self.streamOut2 = FileOutput(self.streamOut)
            self.encoder.output = [self.streamOut2]

            # H264 encoder for recording
            self.h264_encoder = H264Encoder()
            self.output = CircularOutput()

            # Start camera and encoder
            self.camera.start()
            self.camera.start_encoder(self.encoder)
            self.camera.start_recording(self.h264_encoder, self.output)

            logger.info("Camera initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}")
            self.camera = None

    def get_frame(self):
        """Get a single frame from the camera"""
        if not self.camera:
            logger.error("Camera not initialized.")
            return None

        try:
            with self.streamOut.condition:
                self.streamOut.condition.wait()
                frame = self.streamOut.frame
            return frame
        except Exception as e:
            logger.error(f"Error getting frame: {e}")
            return None

    def video_snap(self):
        """Take a still photo"""
        if not self.camera:
            logger.error("Camera not initialized.")
            return False

        try:
            timestamp = datetime.now().isoformat("_", "seconds")
            logger.info(f"Taking photo at {timestamp}")

            filename = os.path.join(CONFIG['PICTURE_DIR'], f"snap_{timestamp}.jpg")
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            self.still_config = self.camera.create_still_configuration()
            time.sleep(1)  # Allow camera to adjust

            job = self.camera.switch_mode_and_capture_file(
                self.still_config, filename, wait=False
            )
            self.camera.wait(job)
            logger.info(f"Photo saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Error taking photo: {e}")
            return False

    def start_recording(self, basename):
        """Start video recording"""
        if not self.camera:
            logger.error("Camera not initialized.")
            return False

        try:
            os.makedirs(CONFIG['VIDEO_DIR'], exist_ok=True)
            output_file = os.path.join(CONFIG['VIDEO_DIR'], f"Bird_{basename}.h264")
            self.output.fileoutput = output_file
            self.output.start()
            logger.info(f"Started recording to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            return False

    def stop_recording(self):
        """Stop video recording"""
        if not self.camera:
            logger.error("Camera not initialized.")
            return False

        try:
            self.output.stop()
            logger.info("Recording stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping recording: {e}")
            return False

    def cleanup(self):
        """Clean up camera resources"""
        if self.camera:
            try:
                self.camera.stop_encoder()
                self.camera.stop()
                logger.info("Camera resources released")
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}")

# ========================= Frame Generator =========================
def gen_frames(camera):
    """Generate a sequence of frames for video streaming"""
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            time.sleep(0.1)  # Avoid busy wait if camera not working

# ========================= Helper Functions =========================
def show_time():
    """Return current time formatted for file names"""
    now = datetime.now()
    formatted_time = now.strftime("%d-%m-%Y_%H:%M:%S")
    logger.debug(f"Timestamp created: {formatted_time}")
    return formatted_time

def record_audio(duration=30):
    """Record audio for the specified duration"""
    try:
        timestamp = datetime.now().isoformat("_", "seconds")
        os.makedirs(CONFIG['SOUND_DIR'], exist_ok=True)

        command = (
            f'arecord -D dmic_sv -d {duration} -r 48000 -f S32_LE '
            f'{CONFIG["SOUND_DIR"]}birdcam_$(date "+%b-%d-%y-%I:%M:%S-%p").wav -c 2'
        )
        subprocess.Popen(command, shell=True)
        logger.info(f"Started audio recording at {timestamp}")
        return True
    except Exception as e:
        logger.error(f"Error recording audio: {e}")
        return False

# ========================= Flask App Setup =========================
app = Flask(__name__, template_folder='template', static_url_path='/static')
api = Api(app)

# Initialize camera
camera = Camera() if CAMERA_AVAILABLE else None

# Register cleanup handler
@atexit.register
def cleanup_resources():
    """Clean up resources when application exits"""
    if camera:
        camera.cleanup()
    logger.info("Application shutting down, resources released")

# ========================= Flask Routes =========================
@app.route('/')
@app.route('/home')
def index():
    """Video streaming home page"""
    return render_template('index.html')

@app.route('/info.html')
def info():
    """Info page"""
    return render_template('info.html')

@app.route('/startRec.html')
def start_rec():
    """Start recording video"""
    logger.info("Video recording requested")
    basename = show_time()
    if camera:
        camera.start_recording(basename)
    return render_template('startRec.html')

@app.route('/stopRec.html')
def stop_rec():
    """Stop recording video"""
    logger.info("Video recording stop requested")
    if camera:
        camera.stop_recording()
    return render_template('stopRec.html')

@app.route('/srecord.html')
def srecord():
    """Record audio"""
    logger.info("Audio recording requested")
    record_audio(30)
    return render_template('srecord.html')

@app.route('/snap.html')
def snap():
    """Take a photo"""
    logger.info("Photo capture requested")
    if camera:
        camera.video_snap()
    return render_template('snap.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    if not camera:
        return "Camera not available", 500
    return Response(
        gen_frames(camera),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )\

@app.route('/stream')
def video_stream():
    # rtsp_url = f"rtsp://pi5.local:8554/{stream_name}"
    # encoder = H264Encoder(bitrate=4_000_000)
    # rtsp_out = FfmpegOutput(rtsp_url, audio=False)
    # camera.start_recording(encoder, rtsp_out)
    # return f"Publishing started to {rtsp_url}"
    """Start publishing the live H.264 to the hub via RTSP without restarting the encoder."""
    if not camera or not camera.camera:
        return "Camera not available", 500
    try:
        # Build the RTSP target (uses globals defined above)
        rtsp_url_local = f"rtsp://pi5.local:8554/{stream_name}"
        rtsp_out = FfmpegOutput(rtsp_url_local, audio=False)
        # Append publish output to the existing H.264 encoder outputs
        outs = camera.h264_encoder.output
        if not isinstance(outs, (list, tuple)):
            outs = [outs]
        outs = [o for o in outs if o is not None]
        outs.append(rtsp_out)
        camera.h264_encoder.output = outs

        logger.info(f"publishing started to {rtsp_url_local}")
        return f"Publiching started to {rtsp_url_local}"
    except Exception as e:
        logger.exception("Failed to start publishing")
        return f"Failed to start publishing: {e}", 500


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