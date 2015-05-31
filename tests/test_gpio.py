import unittest

from mock import patch

from weathervane.gpio import GPIO


@patch('weathervane.gpio.GPIO.load_library_by_name')
class TestGPIO(unittest.TestCase):
    def test_init_both_pins_and_spi(self, mock_loader):
        gpio = GPIO(channel=0, frequency=500000, library='wiringPi', ready_pin=4)
        # gpio.handle.wiringPiSetup.assert_called_once_with()
        gpio.handle.wiringPiSPISetup.assert_called_once_with(0, 500000)

    def test_gpio_context_manager(self, mock_loader):
        with GPIO(channel=0, frequency=10000, library='None', ready_pin=0).interrupt() as g:
            result, length = g.pack('a')

        self.assertEqual(list(result), [ord('a')])

    def test_constructor(self, mock_loader):
        test = None

        with GPIO(channel=0, frequency=0, library='wiringPi', ready_pin=0).interrupt() as g:
            self.assertTrue(g)