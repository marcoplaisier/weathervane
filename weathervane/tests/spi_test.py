import unittest
import logging
import bitstring

from mock import MagicMock, patch

from weathervane.gpio import GPIO, SPISetupException, SPIDataTransmissionError


__author__ = 'Marco'


class SpiTests(unittest.TestCase):
    def setUp(self):
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    def test_initialization_wrong_channel(self):
        self.assertRaises(SPISetupException, GPIO, channel=2, frequency=25000, library='wiringPi')

    def test_initialization_non_existing_lib(self):
        self.assertRaises(SPISetupException, GPIO, library='not-existing-here', channel=0, frequency=25000)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_initialization(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_empty_list(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        data = []
        data_packet, length = spi.pack(data)
        self.assertEqual([], list(data_packet))
        self.assertEqual(0, length)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_one_element(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        data = [1]
        data_packet, length = spi.pack(data)
        self.assertEqual([1], list(data_packet))
        self.assertEqual(1, length)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_two_elements(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        data = [1, 2]
        data_packet, length = spi.pack(data)
        self.assertEqual([1, 2], list(data_packet))
        self.assertEqual(2, length)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_iterable(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        it = range(0, 10)
        data_packet, length = spi.pack(data=it)
        self.assertEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], list(data_packet))
        self.assertEqual(len(it), length)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_large_bytes(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        data = [-10, -1, 0, 255, 256, 266]
        self.assertRaises(ValueError, spi.pack, data=data)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_pack_with_iterable(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        data = range(0, 4)
        data_packet, length = spi.pack(data)
        self.assertEqual([0, 1, 2, 3], list(data_packet))
        self.assertEqual(4, length)

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_transmission(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        spi.handle.wiringPiSPIDataRW = MagicMock()
        spi.handle.wiringPiSPIDataRW.return_value = 0
        data = [1]
        spi.send_data(data)
        spi.handle.wiringPiSPIDataRW.assert_called_once()

    @patch('weathervane.gpio.GPIO.load_library_by_name')
    def test_incorrect_return_code(self, mock_class):
        spi = GPIO(channel=0, frequency=25000, library='wiringPi', ready_pin=4)
        spi.handle.wiringPiSPIDataRW = MagicMock()
        spi.handle.wiringPiSPIDataRW.return_value = -1
        data = bitstring.pack('uint:4', 1)
        self.assertRaises(SPIDataTransmissionError, spi.send_data, data)

if __name__ == '__main__':
    unittest.main()