import unittest
from mock import Mock, patch
from weathervane.gpio import GPIO


@patch('weathervane.gpio.GPIO.load_library_by_name')
class TestGPIO(unittest.TestCase):
    def test_init_both_pins_and_spi(self, mock_class):
        gpio = GPIO(channel=0, frequency=500000, library='wiringPi', ready_pin=4)
        gpio.handle.wiringPiSetup.assert_called_once_with()
        gpio.handle.wiringPiSPISetup.assert_called_once_with(0, 500000)