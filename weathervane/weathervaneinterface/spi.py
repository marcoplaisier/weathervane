from ctypes import cdll, c_ubyte

__author__ = 'marco'

class SetupException(Exception):
    pass

class DataTransmissionError(Exception):
    pass

class spi(object):
    def __init__(self, library='wiringPi'):
        lib_name = 'wiringPi'
        self.handle = cdll.LoadLibrary(lib_name)

    def setup(channel=0, frequency=500000):
        return_code = self.handle.wiringPiSPISetup(channel, frequency)
        if return_code < -1:
            raise SetupException('Could not setup SPI protocol.')

    def send_data(data):
        data_list = c_ubyte*len(data)
        return_code = self.handle.wiringPiSPIDataRW(0, data_list, len(data))
        if return_code < -1:
            raise DataTransmissionError('Problem with transmission')
        return data_list