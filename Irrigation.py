from flask import Flask, render_template, request
import sys

if sys.platform == 'linux':
    import RPi.GPIO as GPIO
else:
    # Mock RPi.GPIO for development on non-Raspberry Pi platforms
    class MockGPIO:
        BCM = 'BCM'
        OUT = 'OUT'
        IN = 'IN'
        HIGH = 'HIGH'
        LOW = 'LOW'

        def setmode(self, mode):
            print(f"GPIO mode set to {mode}")

        def setup(self, channel, mode):
            print(f"GPIO channel {channel} set up as {mode}")

        def output(self, channel, state):
            print(f"GPIO channel {channel} output set to {state}")

        def input(self, channel):
            return self.LOW

        def cleanup(self):
            print("GPIO cleanup called")


    GPIO = MockGPIO()

app = Flask(__name__)

GPIO.setmode(GPIO.BCM)
pump_pin = 17
GPIO.setup(pump_pin, GPIO.OUT)

@app.route('/pump', methods=['POST'])
def control_pump():
    action = request.form.get('action')
    if action == 'on':
        GPIO.output(pump_pin, GPIO.HIGH)
        return 'Pump turned ON', 200
    elif action == 'off':
        GPIO.output(pump_pin, GPIO.LOW)
        return 'Pump turned OFF', 200
    else:
        return 'Invalid action', 400

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5001)
    finally:
        GPIO.cleanup()