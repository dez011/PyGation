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


# rest of your program

app = Flask(__name__)

def generate_frames():
    camera = Picamera2()
    camera.resolution = (640, 480)
    camera.framerate = 24
    stream = io.BytesIO()

    for _ in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
        stream.seek(0)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.read() + b'\r\n'
        stream.seek(0)
        stream.truncate()

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)

