import logging
from ctypes import c_ubyte, cdll, util
from unittest.mock import Mock


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

    def __init__(self, *args, **kwargs):
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
        self.channel = kwargs["channel"]
        self.frequency = kwargs["frequency"]
        self.library = kwargs["library"]

        if self.channel not in self.AVAILABLE_CHANNELS:
            # If the channel is not 0 or 1, the rest of the program may fail silently or give weird errors. So, we
            # raise an exception.
            error_message = (
                "Channel must be 0 or 1. Channel {} is not available".format(self.channel)
            )
            logging.exception(error_message)
            raise SPISetupException(error_message)

        if not kwargs.get("test", False):
            try:
                self.handle = self.load_library_by_name(self.library)
                self._setup(self.channel, self.frequency)
                self.data = None
            except SPISetupException as e:
                logging.exception(
                    "Could not setup SPI protocol. Library: {}, channel: {}, frequency: {}. Please run "
                    '"gpio load spi" or install the drivers first'.format(
                        self.library, self.channel, self.frequency
                    )
                )
                raise
        else:
            self.handle = Mock()
            self.read_pin = Mock(return_value=[1, 1])

    @staticmethod
    def load_library_by_name(library):
        """Finds and loads the given library by name.

        Only works on Linux.

        @param library: the name of the library that is sought
        @return: a handle to the library that can be used to call methods and functions in that library
        """

        lib_name = util.find_library(library)
        if lib_name is not None:
            return cdll.LoadLibrary(lib_name)
        else:
            raise SPISetupException("Could not find library {}.".format(library))

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
            error_message = "Could not setup SPI protocol. Status code: {}".format(
                status_code
            )
            logging.exception(error_message)
            raise SPISetupException(error_message)
        else:
            logging.info(
                "SPI protocol setup succeeded at channel {} with frequency {}".format(
                    channel, frequency
                )
            )

        status_code = self.handle.wiringPiSetupGpio()

        if status_code == self.ERROR_CODE:
            error_message = "Could not setup pins. Status code: {}".format(status_code)
            logging.exception(error_message)
            raise SPISetupException(error_message)
        else:
            logging.info("Pins successfully configured")

    def pack(self, data):
        """
        Pack the data in an array of bytes, ready for transmission

        @param data: iterable with bytes
        @return: array of c_ubytes
        """
        # noinspection PyTypeChecker
        data_list = c_ubyte * len(data)
        # noinspection PyCallingNonCallable
        self.data = data_list.from_buffer(bytearray(data))

        return self.data, len(self.data)

    def send_data(self, data):
        """Send data over the 'wire'

        @param data: an iterable that returns only bytes (0 - 255). If the value is outside this range, then
        value = value mod 256. So -10 will be 246, 257 will be 1 and so on.
        @raise SPIDataTransmissionError:
        """

        data_packet, data_length = self.pack(data)

        return_code = self.handle.wiringPiSPIDataRW(self.channel, data_packet, data_length)
        if return_code == self.ERROR_CODE:
            raise SPIDataTransmissionError(
                "Transmission failed and resulted in an error. Data: {}, data length: {}".format(
                    list(data_packet), data_length
                )
            )
        # logging.info("Sent {}".format(binary_format(data)))

    def read_pin(self, pin_numbers):
        """Read the values of the supplied sequence of pins and returns them as a list

        Take note that pin numbering on the Raspberry Pi is not straightforward. There are three sorts of numbering in
        use. Four, if you want to get technical. This depends on the way you setup WiringPi.
        First of all, the wiring pi numbering scheme.
        Second, there is the Broadcom numbering scheme.
        Third, uses the physical pin numbers on the P1 connector
        Fourth, only exported pins, but using the same numbering as the second approach.

        We use the second one, because it gives access to more pins.

        Also note that we will set the pinmode of each of the pins to INPUT. So, if you depend on the pins to also
        output, which you shouldn't do, but hey, then these pins will be set to input when this function is finished.
        At the moment, I haven't found any way to determine the current mode of a pin in a Python program. So we will
        restore the pin mode at the end.

        @param pin_numbers: a sequence of pin numbers to be read
        @rtype : the values for the list of pins
        """
        values = []

        for pin_number in pin_numbers:
            self.handle.pinMode(pin_number, self.INPUT)
            pin_state = self.handle.digitalRead(pin_number)
            values.append(pin_state)

        return values

    def write_pin(self, pin_number, value):
        self.handle.pinMode(pin_number, self.OUTPUT)
        self.handle.digitalWrite(pin_number, value)


class TestInterface(object):
    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.gpio = GPIO(channel=channel, frequency=frequency)

    def __repr__(self):
        return "TestInterface(channel=%d, frequency=%d)" % (
            self.channel,
            self.frequency,
        )

    def send(self, data):
        """Send data to the connected SPI device.

        Keyword arguments:
        data -- an enumerable
        """
        data = list(data)
        self.gpio.send_data(data)

    def get_data(self):
        """Return the data sent by the spi device.

        This function returns the data that was sent by the connected SPI device. To get the data that was originally
        sent to that device, use get_sent_data.
        """
        return self.gpio.data


def binary_format(sequence, bytes_per_line=4):
    """Format a sequence as binary bytes

    This function converts a sequence into a nicely formatted string of the binary values. The sequence is first
    converted into a bytearray (which means that only values in the range 0 - 255 are allowed) and then puts each
    bytes_per_line bytes on a single line. Each line is preceded by the number of the bytes. E.g. 0-3.

    @param sequence:
    @return: a string, properly formatted
    """
    array = bytearray(sequence)
    test = []
    for index, item in enumerate(array):
        if index % bytes_per_line == 0:
            test.append("\n{:2} - {:2} ".format(index, index + 3))
        test.append("{:#010b}".format(item)[2:])
    return "|".join(test) + "|"
