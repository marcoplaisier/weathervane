import logging
from unittest.mock import Mock

import spidev

logger = logging.getLogger()


class SPISetupException(Exception):
    pass


class SPIDataTransmissionError(Exception):
    pass


class GPIO(object):
    ERROR_CODE = -1
    AVAILABLE_CHANNELS = (0, 1)

    def __init__(self, *args, **kwargs):
        """
        The constructor makes the protocol ready to send data via the SPI protocol on the pins on the Raspberry Pi.

        @param channel: the Pi can only drive 2 SPI channels, either 0 or 1
        @param frequency: the amount of bits per second that are sent over the channel. See also:
        http://raspberrypi.stackexchange.com/questions/699/what-spi-frequencies-does-raspberry-pi-support
        @raise SPISetupException: when setup cannot proceed, it will raise a setup exception
        """
        self.frequency = kwargs["frequency"]

        if not kwargs.get("test", False):
            spi = spidev.SpiDev()
            spi.open(0, 0)
            spi.max_speed_hz=100000
            self.spi = spi
        else:
            self.spi = Mock()
            self.read_pin = Mock(return_value=[1, 1])

    def send_data(self, data):
        """Send data over the 'wire'

        @param data: an iterable that returns only bytes (0 - 255). If the value is outside this range, then
        value = value mod 256. So -10 will be 246, 257 will be 1 and so on.
        @raise SPIDataTransmissionError:
        """

        self.spi.xfer(data)
        logger.debug("Sent data via SPI")


class TestInterface(object):
    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.gpio = GPIO(channel=channel, frequency=frequency)

    def __repr__(self):
        return "TestInterface(channel=%d, frequency=%d)" % (
            self.channel,
            self.frequency,
        )

    def send(self, data):
        """Send data to the connected SPI device.

        Keyword arguments:
        data -- an enumerable
        """
        data = list(data)
        self.gpio.send_data(data)
