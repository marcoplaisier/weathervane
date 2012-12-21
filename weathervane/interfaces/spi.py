from ctypes import cdll, c_ubyte, util

class SPISetupException(Exception):
    pass

class SPIDataTransmissionError(Exception):
    pass

class spi(object):
    def __init__(self, library='wiringPi'):
        lib_name = util.find_library('wiringPi')
        self.handle = cdll.LoadLibrary(lib_name)

    def setup(self, channel=0, frequency=500000):
        return_code = self.handle.wiringPiSPISetup(channel, frequency)
        if return_code < -1:
            raise SPISetupException('Could not setup SPI protocol.')
        else:
            print 'Setup succeeded'

    def send_data(self, data):
        data_list = c_ubyte*len(data)
        data_list = data_list(*data)

        return_code = self.handle.wiringPiSPIDataRW(0, data_list, len(data))
        if return_code < -1:
            raise SPIDataTransmissionError('Problem with transmission')
        print return_code, data
        self.data_list = data_list

    def get_data(self):
        return self.data_list
