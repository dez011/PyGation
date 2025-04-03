import unittest
from unittest import TestCase
from unittest.mock import MagicMock

from Irrigation import PumpOnCommand, PumpOffCommand


class Test(TestCase):

    def setUp(self):
        self.gpio = MagicMock()
        self.gpio.HIGH = 'HIGH'
        self.gpio.LOW = 'LOW'
        self.pin = 17

    def test_pump_on_command(self):
        command = PumpOnCommand(self.gpio, self.pin)
        command.execute()
        self.gpio.output.assert_called_once_with(self.pin, self.gpio.HIGH)

    def test_pump_off_command(self):
        command = PumpOffCommand(self.gpio, self.pin)
        command.execute()
        print(f"Output called with: {self.gpio.output.call_args}")
        self.gpio.output.assert_called_once_with(self.pin, self.gpio.LOW)

if __name__ == '__main__':
    unittest.main()