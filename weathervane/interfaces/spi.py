from ctypes import cdll, c_ubyte, util

class SPISetupException(Exception):
    pass

class SPIDataTransmissionError(Exception):
    pass

class spi(object):

    def setup(self, library='wiringPi', channel=0, frequency=500000):
        lib_name = util.find_library(library)
        self.handle = cdll.LoadLibrary(lib_name)
        return_code = self.handle.wiringPiSPISetup(channel, frequency)
        if return_code < -1:
            raise SPISetupException('Could not setup SPI protocol.')
        else:
            print 'Setup succeeded'

    def send_data(self, data):
        data_list = c_ubyte*len(data)
        send_data = data_list(*data)

        return_code = self.handle.wiringPiSPIDataRW(0, send_data, len(send_data))
        if return_code < -1:
            raise SPIDataTransmissionError('Problem with transmission')
        self.data = send_data

    def get_data(self):
        return self.data