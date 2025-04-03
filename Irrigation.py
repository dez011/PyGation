import configparser
import time
from threading import Thread

import schedule
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

config = configparser.ConfigParser()
config.read('plants_config.ini')

GPIO.setmode(GPIO.BCM)
# pump_pin = 17
# GPIO.setup(pump_pin, GPIO.OUT)

class Command:
    def execute(self):
        pass
class PumpOnCommand(Command):
    def __init__(self, gpio, pin):
        self.gpio = gpio
        self.pin = pin
    def execute(self):
        self.gpio.output(self.pin, GPIO.HIGH)
class PumpOffCommand(Command):
    def __init__(self, gpio, pin):
        self.gpio = gpio
        self.pin = pin
    def execute(self):
        self.gpio.output(self.pin, GPIO.LOW)

def water_plant(pin, duration):
    PumpOnCommand(GPIO, pin).execute()
    time.sleep(duration * 60)
    PumpOffCommand(GPIO, pin).execute()

def schedule_watering():
    for section in config.sections():
        pin = int(config[section]['pin'])
        start_time = config[section]['start_time']
        end_time = config[section]['end_time']
        interval = int(config[section]['interval'])
        duration = int(config[section]['duration'])

        schedule.every().day.at(start_time).do(water_plant, pin, duration)
        schedule.every(interval).minutes.do(water_plant, pin, duration).until(end_time)

@app.route('/pump', methods=['POST'])
def control_pump():
    action = request.form.get('action')
    pump_pin = int(request.form.get('pin', 17))  # Default to pin 17 if not specified
    if action == 'on':
        command = PumpOnCommand(GPIO, pump_pin)
    elif action == 'off':
        command = PumpOffCommand(GPIO, pump_pin)
    else:
        return 'Invalid action', 400

    command.execute()
    return f'Pump turned {action}', 200

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule_watering()
    schedule_thread = Thread(target=run_schedule)
    schedule_thread.start()
    try:
        app.run(host='0.0.0.0', port=5001)
    finally:
        GPIO.cleanup()

'''
ssh miguelh@192.168.6.14

git -C ~/PyGation pull && python3 ~/PyGation/Irration.py
'''