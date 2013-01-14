from ctypes import cdll, c_ubyte, util

class SPISetupException(Exception):
    pass

class SPIDataTransmissionError(Exception):
    pass

class spi(object):

    def setup(self, library='wiringPi', channel=0, frequency=500000):
        """Setup loads the WiringPi library and sets the important parameters

         Keyword arguments:
         library -- the name of the library to use. Default: wiringPi. This library must be installed and available.
         channel -- the Pi can only drive 2 SPI channels, either 0 or 1
         frequency -- the amount of bits per second that are sent over the channel. See also:
         http://raspberrypi.stackexchange.com/questions/699/what-spi-frequencies-does-raspberry-pi-support

        """
        if channel not in (0, 1):
            raise ValueError('Channel must be 0 or 1; %d is not available' % channel)
        try:
            lib_name = util.find_library(library)
            self.handle = cdll.LoadLibrary(lib_name)
        except:
            raise SPISetupException('Could not setup SPI protocol. Please run gpio load spi or install the drivers first')

        return_code = self.handle.wiringPiSPISetup(channel, frequency)
        if return_code < -1:
            raise SPISetupException('Could not setup SPI protocol.')
        else:
            print 'Setup succeeded'

    def send_data(self, data):
        #noinspection PyTypeChecker
        data_list = c_ubyte*len(data)
        #noinspection PyCallingNonCallable
        send_data = data_list(*data)

        return_code = self.handle.wiringPiSPIDataRW(0, send_data, len(send_data))
        if return_code < -1:
            raise SPIDataTransmissionError('Problem with transmission')
        self.data = send_data

    def get_data(self):
        return self.data