from unittest.mock import MagicMock

import bitstring
import pytest

from weathervane.gpio import GPIO, SPIDataTransmissionError, SPISetupException


def test_initialization_wrong_channel():
    with pytest.raises(SPISetupException):
        GPIO(channel=2, frequency=25000, library="wiringPi")


def test_initialization():
    GPIO(channel=0, frequency=25000, test=True)


def test_transmission():
    spi = GPIO(channel=0, frequency=25000, test=True)
    spi.spi.xfer = MagicMock()
    data = [1]
    spi.send_data(data)
    assert spi.spi.xfer.called

