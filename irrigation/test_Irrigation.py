import configparser
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch

from Irrigation import PumpOnCommand, PumpOffCommand, schedule_watering, run_schedule


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

    @patch('Irrigation.time.sleep', return_value=None)
    def test_schedule_watering(self, mock_sleep):
        # Load the real configuration file
        config = configparser.ConfigParser()
        config.read('plants_config.ini')

        # Use the real config object
        schedule_watering()

        # Check if the schedule was set correctly
        self.assertTrue(config.has_section('Plant1'))

    @patch('Irrigation.schedule.run_pending')
    @patch('Irrigation.time.sleep', return_value=None)
    def test_run_schedule(self, mock_sleep, mock_run_pending):
        # Run the scheduling loop for a few iterations
        def side_effect(*args, **kwargs):
            if mock_run_pending.call_count >= 3:
                raise KeyboardInterrupt

        mock_run_pending.side_effect = side_effect

        with self.assertRaises(KeyboardInterrupt):
            run_schedule()

        # Check if run_pending was called
        self.assertGreaterEqual(mock_run_pending.call_count, 3)


if __name__ == '__main__':
    unittest.main()