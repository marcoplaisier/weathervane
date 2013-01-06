from interfaces.spi import spi

class TestInterface(object):

    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.spi = spi()
        self.spi.setup(channel=channel, frequency=frequency)
        self.data_changed = False
        self.weather_data = {}

    def __repr__(self):
        return "TestInterface(channel=%d, frequency=%d)" % (self.channel, self.frequency)

    def send(self, data):
        """Send data to the connected SPI device.

        Keyword arguments:
        data -- an enumerable
        """
        data = list(data)
        self.spi.send_data(data)

        def get_data(self):
            """Return the data sent by the spi device.

            This function returns the data that was sent by the connected SPI device. To get the data that was originally
            sent to that device, use get_sent_data.
                    """
        return self.spi.get_data()
