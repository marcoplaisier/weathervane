from spi import spi

class WeatherVaneInterface(object):
    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.spi = spi()
        self.spi.setup(channel, frequency)

    def __repr__(self):
        return "Channel: %d, frequency: %d" % \
               (self.channel, self.frequency)

    def send(self, data):
        self.spi.send_data(data)

    def get_data(self):
        return self.spi.get_data()