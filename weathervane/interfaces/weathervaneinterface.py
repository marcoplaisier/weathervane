from weathervane.interfaces.spi import spi

__author__ = 'marco'

class WeatherVaneInterface(object):
    def __init__(self):
        self.spi = spi()
        self.spi.send_data()

    def send(self, data):
        self.spi.send_data(data)

    def get_data(self):
        return self.spi.get_data()