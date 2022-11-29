from unittest.mock import MagicMock, patch

import bitstring
import pytest

from weathervane.gpio import GPIO, SPIDataTransmissionError, SPISetupException


def test_initialization_wrong_channel():
    with pytest.raises(SPISetupException):
        GPIO(channel=2, frequency=25000, library="wiringPi")


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_initialization(mock_class):
    GPIO(channel=0, frequency=25000, library="wiringPi")


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_pack_with_empty_list(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    data = []
    data_packet, length = spi.pack(data)
    assert [] == list(data_packet)
    assert length == 0


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_pack_with_one_element(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    data = [1]
    data_packet, length = spi.pack(data)
    assert [1] == list(data_packet)
    assert 1 == length


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_pack_with_two_elements(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    data = [1, 2]
    data_packet, length = spi.pack(data)
    assert [1, 2] == list(data_packet)
    assert 2 == length


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_pack_with_iterable(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    it = list(range(0, 10))
    data_packet, length = spi.pack(data=it)
    assert [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] == list(data_packet)
    assert len(it) == length


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_pack_with_large_bytes(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    data = [-10, -1, 0, 255, 256, 266]
    with pytest.raises(ValueError):
        spi.pack(data=data)


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_transmission(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    spi.handle.wiringPiSPIDataRW = MagicMock()
    spi.handle.wiringPiSPIDataRW.return_value = 0
    data = [1]
    spi.send_data(data)
    assert spi.handle.wiringPiSPIDataRW.called


@patch("weathervane.gpio.GPIO.load_library_by_name")
def test_incorrect_return_code(mock_class):
    spi = GPIO(channel=0, frequency=25000, library="wiringPi")
    spi.handle.wiringPiSPIDataRW = MagicMock()
    spi.handle.wiringPiSPIDataRW.return_value = -1
    data = bitstring.pack("uint:4", 1)
    with pytest.raises(SPIDataTransmissionError):
        spi.send_data(data)
