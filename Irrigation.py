from flask import Flask, request
import sys

from Mock_GPIO import MockGPIO

if sys.platform == 'linux':
    print("Running on Raspberry Pi, using RPi.GPIO")
    import RPi.GPIO as GPIO
else:
    # Mock RPi.GPIO for development on non-Raspberry Pi platforms
    print("Running on non-Raspberry Pi platform, using mock GPIO")

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

'''
ssh miguelh@192.168.6.14

git -C ~/PyGation pull && python3 ~/PyGation/Irration.py
'''