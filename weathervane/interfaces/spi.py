from ctypes import cdll, c_ubyte

__author__ = 'marco'

class SPISetupException(Exception):
    pass

class SPIDataTransmissionError(Exception):
    pass

class spi(object):
    def __init__(self, library='wiringPi'):
        lib_name = 'wiringPi'
        self.handle = cdll.LoadLibrary(lib_name)

    def __repr__(self):
        return
    def setup(self, channel=0, frequency=500000):
        return_code = self.handle.wiringPiSPISetup(channel, frequency)
        if return_code < -1:
            raise SPISetupException('Could not setup SPI protocol.')

    def send_data(self, data):
        data_list = c_ubyte*len(data)
        return_code = self.handle.wiringPiSPIDataRW(0, data_list, len(data))
        if return_code < -1:
            raise SPIDataTransmissionError('Problem with transmission')
        self.data_list = data_list

    def get_data(self):
        return self.data_list