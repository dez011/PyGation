import atexit
import os
import subprocess
import time
from datetime import datetime

from flask import render_template, Response

from piSecureKit.main import logger, CONFIG, camera, app, stream_name

import logging
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

def gen_frames(_camera):
    """Generate a sequence of frames for video streaming"""
    while True:
        frame = _camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            time.sleep(0.1)  # Avoid busy wait if camera not working


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


@atexit.register
def cleanup_resources():
    """Clean up resources when application exits"""
    if camera:
        camera.cleanup()
    logger.info("Application shutting down, resources released")


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
    )


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
