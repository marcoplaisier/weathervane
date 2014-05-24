__author__ = 'marcoplaisier'

import unittest
from mock import patch, Mock
from weathervane.gpio import Pin


class PinTest(unittest.TestCase):
    @patch('weathervane.gpio.SPI.load_library_by_name')
    def test_pin_read(self, mock_class):
        pin = Pin(0, Pin.INPUT)
        result = pin.read()
        pin.spi.handle.digitalRead.assert_called_with(0)