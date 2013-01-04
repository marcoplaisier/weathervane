from spi import spi

class WeatherVaneInterface(object):
    DATA_CHANGED = int(0b10000000)
    DATA_UNCHANGED = int(0b00000000)

    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.spi = spi()
        self.spi.setup(channel=channel, frequency=frequency)
        self.data_changed = None
        self.data = []

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % \
               (self.channel, self.frequency)

    def send(self, data):
        """Send data to the connected SPI device.

        Keyword arguments:
        data -- an iterable
        """
        s1 = set(data)
        s2 = set(self.data)

        self.data = data #save original data to avoid comparing the toggle bit with s1 and s2
        data = list(data) #convert to a list, so the toggle bit can be appended even if it was an immutable

        if s1.difference(s2):
            data.append(self.DATA_CHANGED)
            self.data_changed = True
        else:
            data.append(self.DATA_UNCHANGED)
            self.data_changed = False
        self.spi.send_data(data)


    def get_data(self):
        """Return the data sent by the spi device.

        This function returns the data that was sent by the connected SPI device. To get the data that was originally
        sent to that device, use get_sent_data.
                """
        return self.spi.get_data()

    def get_sent_data(self):
        """Return the original data sent to the spi device.

        This function returns the data that was sent to the connected SPI device. To get the data that was returned by
        that device, use get_data().

        Note that the data that actually reached the connected SPI device may have been altered due to all kinds of
        transmission errors. This function does not actually return the data that reached the device.
        """
        return self.data
