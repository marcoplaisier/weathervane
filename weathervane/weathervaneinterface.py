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
        self.old_bit_string = None
        self.new_bit_string = None
        self.weather_data = {}
        self.requested_data = kwargs['bits']
        self.station_bits = kwargs['stations']['pins']
        self.stations = kwargs['stations']['config']

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % (self.channel, self.frequency)

    @property
    def data_changed(self):
        return self.old_bit_string != self.new_bit_string

    def format_string(self):
        fmt = []
        for i, data in enumerate(self.requested_data):
            formatting = self.requested_data[str(i)]
            s = "uint:{0}={1}".format(formatting['length'], formatting['key'])
            fmt.append(s)

        return fmt

    def __convert_data(self, weather_data):
        fmt = self.format_string()
        data, error = self.transmittable_data(weather_data, self.requested_data)
        b = bitstring.pack(fmt, **data)
        return b

    def send(self, weather_data):
        """Send data to the connected SPI device.

        Keyword arguments:
        weather_data -- a named_tuple with the data
        """
        data_array = self.__convert_data(weather_data)
        logging.debug("Sending data: {}".format(data_array))
        self.gpio.send_data(data_array)
        self.old_bit_string, self.new_bit_string = self.new_bit_string, data_array

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

    def transmittable_data(self, weather_data, requested_data):
        result = {}
        error = False
        index = 0

        for key, fmt in requested_data.items():
            measurement_name = requested_data[key]['key']
            value = weather_data.get(fmt['key'], 0)

            if measurement_name == 'wind_direction':
                if value in self.WIND_DIRECTIONS:
                    result['wind_direction'] = self.WIND_DIRECTIONS[value]
                else:
                    logging.debug('Wind direction {} not found. Using North as substitute.'.format(result['wind_direction']))
                    result['wind_direction'] = 0
                    error = True
            else:
                min_value = float(fmt.get('min', 0))
                max_value = float(fmt.get('max', 255))
                step_value = float(fmt.get('step', 1))

                if value < min_value:
                    value = min_value
                    error = True
                    logging.debug('Value {} for {} is smaller than minimum {}'
                                  .format(value, measurement_name, min_value))
                if max_value < value:
                    value = max_value
                    error = True
                    logging.debug('Value {} for {} is larger than maximum {}'
                                  .format(value, measurement_name, max_value))
                try:
                    value -= min_value
                    value /= step_value
                    value = int(value)
                except TypeError:
                    value = 0
                    error = True
                    logging.debug('Value {} for {} is not a number'
                                  .format(value, measurement_name))

                result[fmt['key']] = value

            index += 1

        try:
            wind_speed = result['wind_speed']
            wind_speed_max = result['wind_speed_max']
            if wind_speed > result['wind_speed_max']:
                result['wind_speed'] = wind_speed_max
                error = True
                logging.debug(
                    'Regular wind speed {} may not exceed maximum wind speed {}'
                    .format(wind_speed, wind_speed_max))
        except KeyError:
            pass
        return result, error