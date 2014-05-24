from ctypes import cdll, c_ubyte, util
import logging


class SPISetupException(Exception):
    pass


class SPIDataTransmissionError(Exception):
    pass


class GPIO(object):
    ERROR_CODE = -1
    AVAILABLE_CHANNELS = (0, 1)
    INPUT = 0
    OUTPUT = 1
    PWM_OUTPUT = 2
    GPIO_CLOCK = 3

    def __init__(self, library='wiringPi', channel=0, frequency=500000):
        """
        The constructor makes the protocol ready to send data via the SPI protocol on the pins on the Raspberry Pi.

        The constructor does several things:
        - It loads the WiringPi library
        - It sets the important parameters
        - It handles the setup phase of the WiringPi library
        If the constructor succeeds, then data can be sent with send_data.

        @param library: the name of the library to use. Default: wiringPi. This library must be installed and available.
        @param channel: the Pi can only drive 2 SPI channels, either 0 or 1
        @param frequency: the amount of bits per second that are sent over the channel. See also:
        http://raspberrypi.stackexchange.com/questions/699/what-spi-frequencies-does-raspberry-pi-support
        @raise SPISetupException: when setup cannot proceed, it will raise a setup exception
        """

        if channel not in self.AVAILABLE_CHANNELS:
            # If the channel is not 0 or 1, the rest of the program may fail silently or give weird errors. So, we
            # raise an exception.
            error_message = 'Channel must be 0 or 1. Channel {} is not available'.format(channel)
            logging.exception(error_message)
            raise SPISetupException(error_message)

        try:
            self.handle = self.load_library_by_name(library)
            self._setup(channel, frequency)
            self.data = None
        except SPISetupException:
            logging.exception('Could not setup SPI protocol. Library: {}, channel: {}, frequency: {}. Please run '
                              '"gpio load spi" or install the drivers first'.format(library, channel, frequency))
            raise

    @staticmethod
    def load_library_by_name(library):
        """
        Finds and loads the given library by name.

        Only works on Linux and not on Windows.

        @param library: the name of the library that is sought
        @return: a handle to the library that can be used to call methods and functions in that library
        """

        lib_name = util.find_library(library)
        if lib_name is not None:
            return cdll.LoadLibrary(lib_name)
        else:
            raise SPISetupException(
                'Could not find library {}.'.format(library))

    def _setup(self, channel, frequency):
        """
        Setup the protocol library in order to send data.

        @param channel: the data is sent through a channel. This is just a property of the SPI protocol.
        @param frequency: the amount of bits per second that data can be sent through the pins.
        @raise SPISetupException: if the setup fails (ie. the Wiring Pi returns an error code), then this error is
        raised. There is probably not a lot that can be done when this happens, other than instantiating a new SPI
        object.
        """
        status_code = self.handle.wiringPiSPISetup(channel, frequency)

        if status_code == self.ERROR_CODE:
            error_message = 'Could not setup SPI protocol. Status code: {}'.format(status_code)
            logging.exception(error_message)
            raise SPISetupException(error_message)
        else:
            logging.info('SPI protocol setup succeeded at channel {} with frequency {}'.format(channel, frequency))

        status_code = self.handle.wiringPiSetup()


    def pack(self, data):
        """
        Pack the data in an array of bytes, ready for transmission

        @param data: iterable with bytes
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

        @param data: an iterable that returns only bytes (0 - 255). If the value is outside this range, then
        value = value mod 256. So -10 will be 246, 257 will be 1 and so on.
        @raise SPIDataTransmissionError:
        """

        data_packet, data_length = self.pack(data)

        return_code = self.handle.wiringPiSPIDataRW(0, data_packet, data_length)
        if return_code == self.ERROR_CODE:
            raise SPIDataTransmissionError(
                'Transmission failed and resulted in an error. Data: {}, data length: {}'.format(list(data_packet),
                                                                                                 data_length))
        logging.info("Sent {} as {}".format(data, data_packet))

    def get_data(self):
        return self.data
    
    def read_pin(self, pin_numbers):
        for pin_number in pin_numbers:
            self.handle.pinMode(pin_number, self.INPUT)
        return [self.handle.digitalRead(pin_number) for pin_number in pin_numbers]