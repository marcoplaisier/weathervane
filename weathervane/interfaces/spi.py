from ctypes import cdll, c_ubyte, util
import logging


class SPISetupException(Exception):
    pass


class SPIDataTransmissionError(Exception):
    pass


class SPI(object):
    @staticmethod
    def load_library_by_name(library):
        """
        Finds and loads the given library by name

        @param library: the name of the library that is sought
        @return: a handle to the library that can be used to call methods and functions in that library
        """

        lib_name = util.find_library(library)
        if lib_name is not None:
            return cdll.LoadLibrary(lib_name)
        else:
            raise SPISetupException(
                'Could not find library. Please run "gpio load spi" or install the drivers first')

    def setup(self, channel, frequency):
        status_code = self.handle.wiringPiSPISetup(channel, frequency)
        if status_code < -1:
            error_message = 'Could not setup SPI protocol. Status code: {}'.format(status_code)
            logging.exception(error_message)
            raise SPISetupException(error_message)
        else:
            logging.critical('SPI protocol setup succeeded at channel {} with frequency {}'.format(channel, frequency))

    def __init__(self, library='wiringPi', channel=0, frequency=500000):
        """
        Setup loads the WiringPi library and sets the important parameters

        @param library: the name of the library to use. Default: wiringPi. This library must be installed and available.
        @param channel: the Pi can only drive 2 SPI channels, either 0 or 1
        @param frequency: the amount of bits per second that are sent over the channel. See also:
        http://raspberrypi.stackexchange.com/questions/699/what-spi-frequencies-does-raspberry-pi-support
        @raise SPISetupException: when setup cannot proceed, it will raise a setup exception
        """

        if channel not in (0, 1):
            # If the channel is not 0 or 1, the rest of the program may fail silently or give weird errors.
            error_message = 'Channel must be 0 or 1. Channel {} is not available'.format(channel)
            logging.exception(error_message)
            raise SPISetupException(error_message)

        try:
            self.handle = self.load_library_by_name(library)
            self.setup(channel, frequency)
            self.data = None
        except SPISetupException:
            logging.exception('Could not setup SPI protocol. Library: {}, channel: {}, frequency: {}'.
            format(library, channel, frequency))
            raise

    def pack(self, data):
        """
        Pack the data in a array of bytes, ready for transmission

        @param data: list of integers
        @return: array of c_ubytes
        """
        # noinspection PyTypeChecker
        data_list = c_ubyte * len(data)
        # noinspection PyCallingNonCallable
        self.data = data_list(*data)

        return self.data, len(self.data)

    def send_data(self, data):
        """
        Send data over the 'wire'

        @param data:
        @raise SPIDataTransmissionError:
        """

        data_packet, data_length = self.pack(data)

        return_code = self.handle.wiringPiSPIDataRW(0, data_packet, data_length)
        if return_code < -1:
            raise SPIDataTransmissionError(
                'Transmission failed and resulted in an error. Data: {}, data length: {}'.format(data_packet,
                                                                                                 data_length))
        logging.info("Sent {} as {}".format(data, data_packet))

    def get_data(self):
        return self.data