__author__ = 'marcoplaisier'

import unittest
from mock import patch, Mock, call
from weathervane.gpio import GPIO


@patch('weathervane.gpio.GPIO.load_library_by_name')
class PinTest(unittest.TestCase):
    def test_pin_read(self, mock_class):
        interface = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        interface.handle.pinMode.assert_called_once_with(4, 1)
        interface.handle.pinMode.reset_mock()
        interface.read_pin([3])
        interface.handle.pinMode.assert_called_once_with(3, 0)
        interface.handle.digitalRead.assert_called_once_with(3)

    def test_pins_read(self, mock_class):
        interface = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=3)
        interface.read_pin([0, 1, 2])
        setup_calls = [call(0, 0), call(1, 0), call(2, 0)]
        interface.handle.pinMode.assert_has_calls(setup_calls)
        read_calls = [call(0), call(1), call(2)]
        interface.handle.digitalRead.assert_has_calls(read_calls)