import copy
from spi import spi

class WeatherVaneInterface(object):
    WIND_DIRECTIONS = {'N': 0x00, 'NNO': 0x01, 'NO': 0x02, 'ONO': 0x03,
                       'O': 0x04, 'OZO': 0x05, 'ZO': 0x06, 'ZZO': 0x07,
                       'Z': 0x08, 'ZZW': 0x09, 'ZW': 0x0A, 'WZW': 0x0B,
                       'W': 0x0C, 'WNW': 0x0D, 'NW': 0x0E, 'NNW': 0x0F}
    DATA_CHANGED = 0b10000000
    DATA_UNCHANGED = 0b00000000
    DUMMY_BYTE = 0x00
    WIND_DIRECTION_ERROR = 0b00000001
    WIND_SPEED_ERROR = 0b00000010
    AIR_PRESSURE_ERROR = 0b00000100
    WIND_SPEED_MAX_ERROR = 0b00001000
    WIND_SPEED_MINIMUM = 0
    WIND_SPEED_MAXIMUM = 63
    AIR_PRESSURE_MINIMUM = 900
    AIR_PRESSURE_MAXIMUM = 1155

    def __init__(self, channel=0, frequency=50000):
        self.channel = channel
        self.frequency = frequency
        self.spi = spi()
        self.spi.setup(channel=channel, frequency=frequency)
        self.data_changed = False
        self.weather_data = {}

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % (self.channel, self.frequency)

    def __cast_wind_direction_to_byte(self, weather_data, errors):
        try:
            wind_direction_code = weather_data['wind_direction']
            wind_direction_byte = self.WIND_DIRECTIONS[wind_direction_code]
        except KeyError:
            wind_direction_byte = 0x00
            errors |= self.WIND_DIRECTION_ERROR

        return wind_direction_byte, errors

    def __cast_air_pressure_to_byte(self, weather_data, errors):
        try:
            air_pressure = float(weather_data['air_pressure'])
        except (KeyError, ValueError):
            air_pressure = 0x00
            errors |= self.AIR_PRESSURE_ERROR

        if air_pressure < self.AIR_PRESSURE_MINIMUM:
            air_pressure = 0x00
            errors |= self.AIR_PRESSURE_ERROR
        elif self.AIR_PRESSURE_MAXIMUM < air_pressure:
            air_pressure = 0xFF
            errors |= self.AIR_PRESSURE_ERROR
        else:
            air_pressure -= self.AIR_PRESSURE_MINIMUM

        return air_pressure, errors

    def __cast_wind_speed_to_byte(self, weather_data, errors):
        try:
            wind_speed = float(weather_data['wind_speed'])
        except (KeyError, ValueError):
            wind_speed = 0x00
            errors |= self.WIND_SPEED_ERROR

        if wind_speed < self.WIND_SPEED_MINIMUM:
            wind_speed = 0x00
            errors |= self.WIND_SPEED_ERROR
        elif self.WIND_SPEED_MAXIMUM < wind_speed:
            wind_speed = 63
            errors |= self.WIND_SPEED_ERROR

        return wind_speed, errors

    def __cast_wind_speed_max_to_byte(self, weather_data, errors):
        try:
            wind_speed_max = float(weather_data['wind_speed_max'])
        except (KeyError, ValueError):
            wind_speed_max = 0x00
            errors |= self.WIND_SPEED_MAX_ERROR

        if wind_speed_max < self.WIND_SPEED_MINIMUM:
            wind_speed_max = 0x00
            errors |= self.WIND_SPEED_MAX_ERROR
        elif self.WIND_SPEED_MAXIMUM < wind_speed_max:
            wind_speed_max = 63
            errors |= self.WIND_SPEED_MAX_ERROR

        return wind_speed_max, errors

    def __get_data_changed(self, weather_data):
        if weather_data == self.weather_data:
            result = self.DATA_UNCHANGED
            self.data_changed = False
        else:
            result = self.DATA_CHANGED
            self.data_changed = True

        self.weather_data = copy.copy(weather_data)

        return result

    def __convert_data(self, weather_data):
        errors = 0x00

        wind_direction, errors = self.__cast_wind_direction_to_byte(weather_data, errors)
        wind_speed, errors = self.__cast_wind_speed_to_byte(weather_data, errors)
        wind_speed_max, errors = self.__cast_wind_speed_max_to_byte(weather_data, errors)
        air_pressure, errors = self.__cast_air_pressure_to_byte(weather_data, errors)
        service_byte = errors | self.__get_data_changed(weather_data)

        data = [wind_direction, wind_speed, air_pressure, service_byte, self.DUMMY_BYTE]

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

        Returns:
        array of bytes
                """
        return self.spi.get_data()

    def get_sent_data(self):
        """Return the original data sent to the spi device.

        This function returns the data that was sent to the connected SPI device. To get the data that was returned by
        that device, use get_data().

        Note that the data that actually reached the connected SPI device may have been altered due to all kinds of
        transmission errors. This function does not actually return the data that reached the device.

        Returns:
        array of bytes
        """

        return self.weather_data

