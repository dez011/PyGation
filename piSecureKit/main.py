#!/usr/bin/python3

import socket
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

# Initialize Picamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration({"size": (640, 480)})
picam2.configure(video_config)

# Set up H.264 encoder
encoder = H264Encoder(1000000)  # 1 Mbps bitrate

# Create a socket server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", 5000))  # Host and port
    sock.listen()

    print("Waiting for a connection...")
    conn, addr = sock.accept()
    print(f"Connection established with {addr}")

    # Stream H.264 video to the client
    with conn.makefile("wb") as stream:
        encoder.output = FileOutput(stream)
        picam2.start_encoder(encoder)
        picam2.start()
        try:
            while True:
                pass  # Keep streaming until interrupted
        except KeyboardInterrupt:
            print("Streaming stopped.")
        finally:
            picam2.stop()
            picam2.stop_encoder()




# first
import io
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    # noinspection PyUnresolvedReferences
    from picamera2 import Picamera2  # for hints only
from flask import Flask, Response

try:
    # noinspection PyUnresolvedReferences
    from picamera2 import Picamera2   # real on Pi
except Exception:
    class Picamera2:                  # stub on Mac
        def create_video_configuration(self, *_, **__): return object()
        def configure(self, *_): pass
        def start(self): pass
        def capture_array(self):
            import numpy as np, time
            t = int(time.time()*10) % 255
            img = np.zeros((480, 640, 3), np.uint8)
            img[...,0] = t; img[...,1] = (t*2)%255; img[...,2] = (t*3)%255
            return img
        def close(self): pass

        def capture_continuous(self, stream, param, use_video_port):
            while True:
                stream.write(b"dummy_frame_data")
                yield stream
try:
    # noinspection PyUnresolvedReferences
    import cv2  # real on Pi
except ImportError:
    class cv2:  # stub on Mac
        @staticmethod
        def imencode(ext, frame):
            # Simulate successful encoding
            return True, b"dummy_encoded_frame"

# rest of your program

app = Flask(__name__)
picam2 = Picamera2()

# Configure camera (640x480 @ 24fps)
config = picam2.create_video_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array()              # Get numpy array (BGR)
        ret, buffer = cv2.imencode('.jpg', frame)   # Encode as JPEG
        if not ret:
            continue
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, threaded=True)
##first end
##second
# def generate_frames():
#     camera = Picamera2()
#     camera.resolution = (640, 480)
#     camera.framerate = 24
#     stream = io.BytesIO()
#
#     for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
#         stream.seek(0)
#         yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
#         stream.seek(0)
#         stream.truncate()
#
# @app.route('/video_feed')
# def video_feed():
#     return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
#
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, threaded=True)
##second end
