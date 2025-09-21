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

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PiSecureKit')

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
    logger.info("Camera modules loaded successfully")
except ImportError:
    logger.warning("Camera modules not available. Camera functionality will be disabled.")
    CAMERA_AVAILABLE = False

# Configuration constants
HUB = "192.168.6.76"  # Pi5 hub IP (not localhost)
USER = "myuser"
PASS = "mypass"


def setup_camera():
    """Initialize and configure the camera"""
    logger.info("Setting up camera...")
    picam2 = Picamera2()
    frame_rate = 30

    # Create video configurations
    video_config = picam2.create_video_configuration(
        main={"size": (640, 480), "format": "YUV420"},
        lores={"size": (640, 480), "format": "YUV420"},
        controls={'FrameRate': frame_rate},
        buffer_count=2
    )

    video_config2 = picam2.create_video_configuration(
        main={"size": (1280, 720), "format": "YUV420"},  # compact, encoder-friendly
        lores=None,  # turn OFF extra lores stream
        raw=None,  # turn OFF RAW stream (huge CMA hit)
        controls={"FrameRate": 30},
        buffer_count=3  # fewer DMA buffers = less CMA
    )

    picam2.align_configuration(video_config)
    picam2.configure(video_config2)
    logger.info("Camera configured successfully")

    return picam2, frame_rate, video_config, video_config2


def setup_streaming(hub_ip):
    """Set up streaming components"""
    logger.info("Configuring streaming outputs and encoders")

    # RTSP Output configuration
    HQoutput = FfmpegOutput(
        f"-fflags +genpts -use_wallclock_as_timestamps 1 "
        f"-rtsp_transport tcp -muxdelay 0 -muxpreload 0 "
        f"-f rtsp rtsp://{hub_ip}:8554/hqstream",
        audio=False
    )

    # Encoder settings
    encoder_HQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)
    encoder_LQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)

    return encoder_HQ, encoder_LQ, HQoutput


def capture_still_images(picam2):
    """Capture still images at regular intervals"""
    logger.debug("Capturing still image")
    still = picam2.capture_request()
    still.save("main", "/dev/shm/camera-tmp.jpg")
    still.release()
    logger.debug("Still image captured")


def cleanup(picam2):
    """Stop recording and clean up resources"""
    logger.info("Stopping camera recording and cleaning up")
    try:
        picam2.stop_recording()
        logger.info("Camera recording stopped")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


def main():
    """Main application entry point"""
    if not CAMERA_AVAILABLE:
        logger.error("Camera modules not available. Exiting.")
        return

    try:
        # Set up camera
        picam2, frame_rate, video_config, video_config2 = setup_camera()

        # Set up streaming components
        encoder_HQ, encoder_LQ, HQoutput = setup_streaming(HUB)

        # Register cleanup handler
        atexit.register(lambda: cleanup(picam2))

        # Start camera stream
        logger.info("Starting camera stream...")
        picam2.start_recording(encoder_HQ, HQoutput)
        logger.info("Camera stream started successfully")

        # Main loop
        while True:
            time.sleep(5)
            capture_still_images(picam2)

    except KeyboardInterrupt:
        logger.info("Camera operation interrupted by user")
        cleanup(picam2)
    except Exception as e:
        logger.error(f"Error in camera operation: {e}")
        cleanup(picam2)


if __name__ == "__main__":
    main()

# #!/usr/bin/env python3
# """
# PiSecureKit - Raspberry Pi Camera Security System
# """
#
# # Standard library imports
# import io
# import os
# import time
# import logging
# import subprocess
# import threading
# import atexit
# from datetime import datetime
# from threading import Condition
#
# # Third-party imports
# # from flask import Flask, render_template, Response
# # from flask_restful import Resource, Api
#
# # Camera-specific imports
# try:
#     import picamera2
#     from picamera2 import Picamera2
#     from picamera2.encoders import H264Encoder, MJPEGEncoder, Quality
#     from picamera2.outputs import FileOutput, CircularOutput, FfmpegOutput
#     from libcamera import Transform
#     CAMERA_AVAILABLE = True
# except ImportError:
#     logging.warning("Camera modules not available. Camera functionality will be disabled.")
#     CAMERA_AVAILABLE = False
#
# HUB = "192.168.6.76"        # <-- Pi5 hub IP (not localhost)
# USER = "myuser"
# PASS = "mypass"
#
#
# picam2 = Picamera2()
# frame_rate = 30
# # max resolution is (3280, 2464) for full FoV at 15FPS
# video_config = picam2.create_video_configuration(main={"size": (640, 480), "format": "YUV420"},
#                                                  lores={"size": (640, 480), "format": "YUV420"},
#                                                  controls={'FrameRate': frame_rate}, buffer_count=2)
# video_config2 = picam2.create_video_configuration(
#     main={"size": (1280, 720), "format": "YUV420"},  # compact, encoder-friendly
#     lores=None,         # <- turn OFF extra lores stream
#     raw=None,           # <- turn OFF RAW stream (huge CMA hit)
#     controls={"FrameRate": 30},
#     buffer_count=3      # <- fewer DMA buffers = less CMA
# )
#
# picam2.align_configuration(video_config)
# picam2.configure(video_config2)
#
# # FFMPEG output config
# # HQoutput = FfmpegOutput("-f rtsp -rtsp_transport udp rtsp://myuser:mypass@localhost:8554/hqstream", audio=False)
# # LQoutput = FfmpegOutput("-f rtsp -rtsp_transport udp rtsp://myuser:mypass@localhost:8554/lqstream", audio=False)
#
# # HQoutput = FfmpegOutput("-f rtsp -rtsp_transport tcp rtsp://192.168.6.76:8554/hqstream", audio=False)
# # LQoutput = FfmpegOutput(f"-c:v copy -an -f rtsp -rtsp_transport tcp rtsp://{HUB}:8554/lqstream", audio=False)
#
# #worksv
# # HQoutput = FfmpegOutput(f"-c:v copy -an -f rtsp -rtsp_transport tcp rtsp://{HUB}:8554/hqstream", audio=True)
# # Fixed HQoutput - removed -c:v copy and fixed audio mismatch
# HQoutput = FfmpegOutput(
#     f"-fflags +genpts -use_wallclock_as_timestamps 1 "
#     f"-rtsp_transport tcp -muxdelay 0 -muxpreload 0 "
#     f"-f rtsp rtsp://{HUB}:8554/hqstream",
#     audio=False  # Changed to match -an flag
# )
# # LQoutput = FfmpegOutput(
# #     f"-fflags +genpts -use_wallclock_as_timestamps 1 "
# #     f"-rtsp_transport tcp -muxdelay 0 -muxpreload 0 "
# #     f"-c:v copy -an -f rtsp rtsp://{HUB}:8554/lqstream",
# #     audio=False
# # )
# # LQoutput = FfmpegOutput("-f rtsp -rtsp_transport tcp rtsp://192.168.6.76:8554/lqstream", audio=False)
#
# # Encoder settings
# encoder_HQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)
# # encoder_LQ = H264Encoder(repeat=True, iperiod=30, framerate=frame_rate, enable_sps_framerate=True)
# # Encoder settings (replace your encoder_LQ line)
# encoder_LQ = H264Encoder(bitrate=2_000_000, repeat=True, iperiod=60)
#
# try:
#     print("trying to start camera streams")
#     # picam2.start_recording(encoder_HQ, HQoutput, quality=Quality.LOW)
#     # picam2.start_recording(encoder_LQ, LQoutput, quality=Quality.LOW)
#     # picam2.start_recording(encoder_LQ, LQoutput, quality=Quality.LOW, name="lores")
#     #works
#     # picam2.start_recording(encoder_LQ, HQoutput, name="lores")
#     picam2.start_recording(encoder_HQ, HQoutput)
#     print("Started camera streams")
#     while True:
#         time.sleep(5)
#         still = picam2.capture_request()
#         still.save("main", "/dev/shm/camera-tmp.jpg")
#         # still.save("main", "/home/allzero22/Webserver/webcam/static/pictures/camera-tmp.jpg")
#         # os.rename('/home/allzero22/Webserver/webcam/static/pictures/camera-tmp.jpg',
#         #           '/home/allzero22/Webserver/webcam/static/pictures/camera.jpg')
#         still.release()
#         # os.rename('/dev/shm/camera-tmp.jpg', '/dev/shm/camera.jpg') # make image replacement atomic operation
# except Exception as e:
#     print("exiting picamera2 streamer due to exception:", e)
#     picam2.stop_recording()
