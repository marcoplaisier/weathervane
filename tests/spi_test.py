from mock import patch
from weathervane.interfaces.SPI import SPI, SPISetupException

__author__ = 'Marco'

import unittest


class MyTestCase(unittest.TestCase):
    def test_initialization_wrong_channel(self):
        self.assertRaises(SPISetupException, SPI, channel=2)

    def test_initialization_wrong_lib(self):
        self.assertRaises(SPISetupException, SPI, library='not-existing-here')

    def test_incorrect_return_code(self):
        pass
        #spi = SPI(channel=0, frequency=500000)
        #TODO: add tests


if __name__ == '__main__':
    unittest.main()
