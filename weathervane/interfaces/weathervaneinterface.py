import copy
from spi import spi

class WeatherVaneInterface(object):
    WIND_DIRECTIONS = {'N': 0x00, 'NNO': 0x01, 'NO': 0x02, 'ONO': 0x03,
                       'O': 0x04, 'OZO': 0x05, 'ZO': 0x06, 'ZZO': 0x07,
                       'Z': 0x08, 'ZZW': 0x09, 'ZW': 0x0A, 'WZW': 0x0B,
                       'W': 0x0C, 'WNW': 0x0D, 'NW': 0x0E, 'NNW': 0x0F}
    AIR_PRESSURE_OFFSET = 900
    WIND_SPEED_SELECTOR = 127
    DATA_CHANGED = int(0b10000000)
    DATA_UNCHANGED = int(0b00000000)
    DUMMY_BYTE = int(0x00)
    SERVICE_BITS = {'wind_direction': int(0b00000001),'wind_speed':int(0b00000010),
                    'air_pressure': int(0b00000100), }

    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.spi = spi()
        self.spi.setup(channel=channel, frequency=frequency)
        self.data_changed = False
        self.weather_data = {}

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % \
               (self.channel, self.frequency)

    def __get_wind_direction_byte(self, weather_data):
        wind_direction_code = weather_data.get('wind_direction', 'N')
        wind_direction_byte = self.WIND_DIRECTIONS.get(wind_direction_code, self.DUMMY_BYTE)

        return wind_direction_byte

    def __get_errors(self, weather_data):
        result = 0x00

        for k in weather_data.keys():
            if weather_data.get(k) is None:
                result |= self.SERVICE_BITS.get(k, self.DUMMY_BYTE)

        return result

    def __get_data_changed(self, weather_data):
        if weather_data == self.weather_data:
            result = self.DATA_UNCHANGED
            self.data_changed = False
        else:
            result = self.DATA_CHANGED
            self.data_changed = True

        self.weather_data = copy.copy(weather_data)

        return result

    def __get_service_byte(self, weather_data):
        service_byte = 0x00

        toggle_bit = self.__get_data_changed(weather_data)
        error_bits = self.__get_errors(weather_data)
        service_byte = service_byte | error_bits | toggle_bit

        return service_byte

    def __convert_data(self, weather_data):
        data = []

        data.append(int(self.__get_wind_direction_byte(weather_data)))
        data.append(int(weather_data.get('wind_speed', self.DUMMY_BYTE) & self.WIND_SPEED_SELECTOR))
        data.append(int(weather_data.get('air_pressure', self.DUMMY_BYTE) - self.AIR_PRESSURE_OFFSET))
        data.append(self.__get_service_byte(weather_data))
        data.append(self.DUMMY_BYTE)

        return data

    def send(self, weather_data):
        """Send data to the connected SPI device.

        Keyword arguments:
        weather_data -- a dictionary with the data
        """
        if not isinstance(weather_data, dict):
            raise TypeError("unsupported type %s " %type(weather_data))

        data_array = self.__convert_data(weather_data)

        self.spi.send_data(data_array)

    def get_data(self):
        """Return the data sent by the spi device.

        This function returns the data that was sent by the connected SPI device. To get the data that was originally
        sent to that device, use get_sent_data.
                """
        return self.spi.get_data()

    def get_sent_data(self):
        """Return the original data sent to the spi device.

        This function returns the data that was sent to the connected SPI device. To get the data that was returned by
        that device, use get_data().

        Note that the data that actually reached the connected SPI device may have been altered due to all kinds of
        transmission errors. This function does not actually return the data that reached the device.
        """
        return self.weather_data
