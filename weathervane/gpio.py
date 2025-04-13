import logging
from unittest.mock import Mock

import spidev

logger = logging.getLogger()


class GPIO:
    def __init__(self, *args, **kwargs):
        """
        The constructor creates the SPI object which sends the data.

        @param test: if True, then the GPIO pins are not used. Instead, a mock object is used to simulate the GPIO pins.
        @param bus: the bus number. The Raspberry Pi has 2 SPI buses, 0 and 1. Defaults to 0.
        @param device: the device number. The Raspberry Pi can drive 2 SPI devices on each bus, 0 and 1. Defaults to 0.
        @param frequency: the amount of bits per second that are sent over the channel. See also:
        http://raspberrypi.stackexchange.com/questions/699/what-spi-frequencies-does-raspberry-pi-support
        """
        self.test = kwargs.get("test", False)
        self.bus = kwargs.get("bus", 0)
        self.device = kwargs.get("device", 0)
        self.frequency = kwargs.get("frequency", 100_000)
        if not self.test:
            spi = spidev.SpiDev()
            spi.open(self.bus, self.device)
            spi.max_speed_hz = self.frequency
            self.spi = spi
        else:
            self.spi = Mock()
            self.read_pin = Mock(return_value=[1, 1])

    def __repr__(self):
        return f"GPIO(channel={self.bus}, device={self.device}, frequency={self.frequency}), test mode={self.test}"

    def send_data(self, data: bytes) -> None:
        """Send data over the 'wire'

        @param data: an iterable of bytes, such as a bytearray or bytes
        """
        self.spi.xfer(data)
        logger.debug("Sent data via SPI")
