from unittest.mock import MagicMock

from weathervane.gpio import GPIO


def test_initialization():
    GPIO(channel=0, frequency=25000, test=True)


def test_transmission():
    spi = GPIO(channel=0, frequency=25000, test=True)
    spi.spi.xfer = MagicMock()
    data = [1]
    spi.send_data(data)
    assert spi.spi.xfer.called

