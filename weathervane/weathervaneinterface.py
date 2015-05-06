import copy
import logging
import bitstring

from gpio import GPIO


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
    FIXED_PATTERN = 0b01010000

    def __init__(self, *args, **kwargs):
        self.channel = kwargs['channel']
        self.frequency = kwargs['frequency']
        self.gpio = GPIO(**kwargs)
        # self.gpio.__init__(channel=self.channel, frequency=self.frequency)
        # TODO: check why I put the call to __init__ separately initially
        self.data_changed = False
        self.weather_data = {}
        self.requested_data = kwargs['bits']
        self.station_bits = kwargs['stations']['pins']
        self.stations = kwargs['stations']['config']

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % (self.channel, self.frequency)

    def __cast_wind_direction_to_byte(self, weather_data):
        errors = 0x00

        try:
            wind_direction_code = weather_data.wind_direction
            wind_direction_byte = self.WIND_DIRECTIONS[wind_direction_code]
        except (KeyError, TypeError, AttributeError):
            wind_direction_byte = 0x00
            errors |= self.WIND_DIRECTION_ERROR

        return int(wind_direction_byte), errors

    def __cast_air_pressure_to_byte(self, weather_data):
        errors = 0x00

        try:
            air_pressure = round(float(weather_data.air_pressure), 0)
        except (KeyError, ValueError, TypeError, AttributeError):
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

        return int(air_pressure), errors

    def __cast_wind_speed_to_byte(self, weather_data):
        errors = 0x00

        try:
            wind_speed = round(float(weather_data.wind_speed), 0)
        except (KeyError, ValueError, TypeError, AttributeError):
            wind_speed = 0x00
            errors |= self.WIND_SPEED_ERROR

        if wind_speed < self.WIND_SPEED_MINIMUM:
            wind_speed = 0x00
            errors |= self.WIND_SPEED_ERROR
        elif self.WIND_SPEED_MAXIMUM < wind_speed:
            wind_speed = 63
            errors |= self.WIND_SPEED_ERROR

        return int(wind_speed), errors

    def __cast_wind_speed_max_to_byte(self, weather_data):
        errors = 0x00

        try:
            wind_speed_max = round(float(weather_data.wind_speed_max), 0)
        except (KeyError, ValueError, TypeError, AttributeError):
            wind_speed_max = 0x00
            errors |= self.WIND_SPEED_MAX_ERROR

        if wind_speed_max < self.WIND_SPEED_MINIMUM:
            wind_speed_max = 0x00
            errors |= self.WIND_SPEED_MAX_ERROR
        elif self.WIND_SPEED_MAXIMUM < wind_speed_max:
            wind_speed_max = 63
            errors |= self.WIND_SPEED_MAX_ERROR

        try:
            wind_speed = round(float(weather_data.wind_speed), 0)
        except (KeyError, ValueError, TypeError, AttributeError):
            wind_speed = 0
        if wind_speed_max < wind_speed:
            wind_speed_max = wind_speed

        return int(wind_speed_max), errors

    def __get_data_changed(self, weather_data):
        if weather_data == self.weather_data:
            result = self.DATA_UNCHANGED
            self.data_changed = False
        else:
            result = self.DATA_CHANGED
            self.data_changed = True

        self.weather_data = copy.copy(weather_data)

        return result

    def format_string(self):
        fmt = ''
        for i, data in enumerate(self.station_bits):
            formatting = self.station_bits[str(i)]
            s = "hex:{0}={1},".format(formatting['length'], formatting['key'])
            fmt += s
        return fmt

    def __convert_data(self, weather_data):
        fmt = self.format_string()
        data, error = self.transmittable_data(weather_data)
        return bitstring.pack(fmt, data)

    def send(self, weather_data):
        """Send data to the connected SPI device.

        Keyword arguments:
        weather_data -- a named_tuple with the data
        """
        data_array = self.__convert_data(weather_data)
        logging.debug("Sending data:" + ", ".join(str(x) for x in data_array))
        self.gpio.send_data(data_array)

    def get_data(self):
        """Return the data sent by the spi device.

        This function returns the data that was sent by the connected SPI device. To get the data that was originally
        sent to that device, use get_sent_data.

        Returns:
        array of bytes
                """
        return self.gpio.get_data()

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

    @property
    def selected_station(self):
        bits = self.gpio.read_pin(self.station_bits)
        result = 0
        for index, value in enumerate(bits):
            result += value * 2 ** index

        return self.stations[result]

    def transmittable_data(self, weather_data):
        result = {}
        index = 0
        for key, fmt in self.station_bits.items():
            value = weather_data._asdict().get(fmt['key'], 0)
            if fmt.get('min', 0) <= value <= fmt.get('max', 0):
                error = True

            value -= float(fmt.get('min', 0))
            value /= float(fmt.get('step', 1))
            value = int(value)
            result[fmt['key']] = value
            index += 1

        return result, error