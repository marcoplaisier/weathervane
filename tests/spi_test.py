from mock import MagicMock, patch
import logging
from weathervane.interfaces.spi import SPI, SPISetupException, SPIDataTransmissionError

__author__ = 'Marco'

import unittest


class MyTestCase(unittest.TestCase):
    def setUp(self):
        logger = logging.getLogger()
        logger.setLevel(logging.CRITICAL)

    def test_initialization_wrong_channel(self):
        self.assertRaises(SPISetupException, SPI, channel=2)

    def test_initialization_non_existing_lib(self):
        self.assertRaises(SPISetupException, SPI, library='not-existing-here')

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_initialization(self, mock_class):
        spi = SPI()

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_pack_with_empty_list(self, mock_class):
        spi = SPI()
        data = []
        data_packet, length = spi.pack(data)
        self.assertEqual([], list(data_packet))
        self.assertEqual(0, length)

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_pack_with_one_element(self, mock_class):
        spi = SPI()
        data = [1]
        data_packet, length = spi.pack(data)
        self.assertEqual([1], list(data_packet))
        self.assertEqual(1, length)

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_pack_with_two_elements(self, mock_class):
        spi = SPI()
        data = [1, 2]
        data_packet, length = spi.pack(data)
        self.assertEqual([1, 2], list(data_packet))
        self.assertEqual(2, length)

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_pack_with_string(self, mock_class):
        spi = SPI()
        data = 'test'
        self.assertRaises(TypeError, spi.pack, data)

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_pack_with_iterable(self, mock_class):
        spi = SPI()
        data = range(0, 4)
        data_packet, length = spi.pack(data)
        self.assertEqual([0, 1, 2, 3], list(data_packet))
        self.assertEqual(4, length)

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_transmission(self, mock_class):
        spi = SPI()
        spi.handle.wiringPiSPIDataRW = MagicMock()
        spi.handle.wiringPiSPIDataRW.return_value = 0
        data = [1]
        spi.send_data(data)
        spi.handle.wiringPiSPIDataRW.assert_called_once()

    @patch('weathervane.interfaces.spi.SPI.load_library_by_name')
    def test_incorrect_return_code(self, mock_class):
        spi = SPI()
        spi.handle.wiringPiSPIDataRW = MagicMock()
        spi.handle.wiringPiSPIDataRW.return_value = -1
        data = [1]
        self.assertRaises(SPIDataTransmissionError, spi.send_data, data)



if __name__ == '__main__':
    unittest.main()
