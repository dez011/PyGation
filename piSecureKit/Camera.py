import os
import time
from datetime import datetime

import piSecureKit.utils
from piSecureKit.main import CAMERA_AVAILABLE, logger, CONFIG, StreamingOutput

# Camera-specific imports
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

            piSecureKit.utils.info("Camera initialized successfully")
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
            piSecureKit.utils.info(f"Taking photo at {timestamp}")

            filename = os.path.join(CONFIG['PICTURE_DIR'], f"snap_{timestamp}.jpg")
            os.makedirs(os.path.dirname(filename), exist_ok=True)

            self.still_config = self.camera.create_still_configuration()
            time.sleep(1)  # Allow camera to adjust

            job = self.camera.switch_mode_and_capture_file(
                self.still_config, filename, wait=False
            )
            self.camera.wait(job)
            piSecureKit.utils.info(f"Photo saved to {filename}")
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
            piSecureKit.utils.info(f"Started recording to {output_file}")
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
            piSecureKit.utils.info("Recording stopped")
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
                piSecureKit.utils.info("Camera resources released")
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}")
