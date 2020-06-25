import unittest
from unittest.mock import patch
from weathervane.gpio import GPIO


@patch('weathervane.gpio.GPIO.load_library_by_name')
class TestGPIO(unittest.TestCase):
    def test_init_both_pins_and_spi(self, mock_loader):
        gpio = GPIO(channel=0, frequency=500000, library='wiringPi')
        # gpio.handle.wiringPiSetup.assert_called_once_with()
        gpio.handle.wiringPiSPISetup.assert_called_once_with(0, 500000)

    def test_gpio_context_manager(self, mock_loader):
        g = GPIO(channel=0, frequency=10000, library='None', interrupt=0)
        l = [128]
        result, length = g.pack(l)

        self.assertEqual(list(result), l)

    def test_constructor(self, mock_loader):
        test = None

        g = GPIO(channel=0, frequency=0, library='wiringPi')
        self.assertTrue(g)

    def test_send(self, mock_loader):
        g = GPIO(channel=0, frequency=0, library='None')
        g.send_data('abc'.encode('UTF-16'))