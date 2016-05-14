import logging
from random import randint

import bitstring
import time

from weathervane.gpio import GPIO


class WeatherVaneInterface(object):
    WIND_DIRECTIONS = {'N': 0x00, 'NNO': 0x01, 'NO': 0x02, 'ONO': 0x03,
                       'O': 0x04, 'OZO': 0x05, 'ZO': 0x06, 'ZZO': 0x07,
                       'Z': 0x08, 'ZZW': 0x09, 'ZW': 0x0A, 'WZW': 0x0B,
                       'W': 0x0C, 'WNW': 0x0D, 'NW': 0x0E, 'NNW': 0x0F}

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
        """Return whether or not the data was different the last time it was sent.

        @return: a boolean indicating whether the data has changed
        """
        return self.old_bit_string != self.new_bit_string

    @property
    def selected_station(self):
        """Return the selected station, based on the station-pins in the stations section of the configuration.

        In the station section of the configuration, it is possible to configure zero or more pins and the corresponding
        stations. Pins are added bitwise and the resulting number is used to lookup the station id.
        For example, in the configuration pin 11 and 13 are indicated as station input pins and four stations are listed:
        0=6000, 1=6001, 2=6002, 3=6003. If pin 13 is high, this results in 0*2**1+1*2**0=1 and id 6001 is returned. If
        pin 11 and 13 are both high, then station 6003 is returned.
        Take note that the order is most significant bit first and that the order of the pin numbers is important. Also
        take care to give an appropriate number of stations. If you indicate two pins and only supply three stations,
        then an index error may be thrown when both pins are high.

        @return: the station id
        """
        bits = self.gpio.read_pin(self.station_bits)
        result = 0
        for index, value in enumerate(bits):
            result += value * 2 ** index

        station_id = self.stations[result]
        return station_id

    def convert_data(self, weather_data):
        """Converts the weather data into a string of bits

        The display is based on a relatively simple programmable interrupt controller (or PIC) when compared to a
        Raspberry PI. It only speaks binary, which means that we need to convert the dictionary with weather data into a
        sequence of bits, before it can be transmitted.
        This conversion is based on four principles:
        # The amount of bits available for each data element is fixed
        # Each element in the data has a minimum value
        # Each element has a maximum value
        # Each element can vary only in discrete steps

        @precondition: the member 'requested data' is properly set
        @param weather_data: a dictionary containing the weatherdata
        @return: a bitstring with the data in bits according to the configuration
        """
        s = None
        t_data = self.transmittable_data(weather_data, self.requested_data)

        for i, data in enumerate(self.requested_data):
            formatting = self.requested_data[str(i)]
            bit_length = int(formatting['length'])
            bit_key = formatting['key']
            bit_value = t_data[bit_key]
            padding_string = '#0{0}b'.format(bit_length + 2)  # don't forget to account for '0b' in the length
            padded_bit_value = format(bit_value, padding_string)
            if s is not None:
                s += bitstring.pack("bin:{}={}".format(bit_length, padded_bit_value))
            else:
                s = bitstring.pack("bin:{}={}".format(bit_length, padded_bit_value))

        return s

    def send(self, weather_data):
        """Send data to the connected SPI device.

        Keyword arguments:
        weather_data -- a dictionary with the data
        """
        data_array = self.convert_data(weather_data)
        self.gpio.send_data(data_array.tobytes())
        self.old_bit_string, self.new_bit_string = self.new_bit_string, data_array

    @property
    def data(self):
        """Return the data sent by the spi device.

        This function returns the data that was sent by the connected SPI device. To get the data that was originally
        sent to that device, use get_sent_data.

        Returns:
        array of bytes
                """
        return self.gpio.data

    @property
    def sent_data(self):
        """Return the original data sent to the spi device.

        This function returns the data that was sent to the connected SPI device. To get the data that was returned by
        that device, use get_data().

        Note that the data that actually reached the connected SPI device may have been altered due to all kinds of
        transmission errors. This function does not actually return the data that reached the device.

        Returns:
        array of bytes
        """

        return self.weather_data

    def transmittable_data(self, weather_data, requested_data):
        result = {}

        for key, fmt in list(requested_data.items()):
            measurement_name = requested_data[key]['key']
            value = weather_data.get(fmt['key'], 0)
            if measurement_name == 'random':
                length = int(requested_data[key]['length'])
                value = randint(0, 2 ** length - 1)

            result[measurement_name] = self.value_to_bits(measurement_name, value, fmt)
            result = self.compensate_wind(result)

        return result

    def value_to_bits(self, measurement_name, value, fmt):
        if measurement_name == 'wind_direction':
            if value in self.WIND_DIRECTIONS:
                return self.WIND_DIRECTIONS[value]
            else:
                logging.debug('Wind direction {} not found. Using North as substitute.'.format(value))
                return 0
        elif measurement_name == 'rain':
            if value > 0:
                return 1
            else:
                return 0
        else:
            step_value = float(fmt.get('step', 1))
            min_value = float(fmt.get('min', 0))
            max_value = float(fmt.get('max', 255))

            if value < min_value:
                logging.debug('Value {} for {} is smaller than minimum {}'.format(value, measurement_name, min_value))
                value = min_value
            if max_value < value:
                logging.debug('Value {} for {} is larger than maximum {}'.format(value, measurement_name, max_value))
                value = max_value

            try:
                value -= min_value
                value /= float(step_value)
            except TypeError:
                logging.debug('Value {} for {} is not a number'.format(value, measurement_name))
                return 0

            return int(value)

    def compensate_wind(self, result):
        wind_speed = result.get('wind_speed', 0)
        wind_speed_max = result.get('wind_speed_max', wind_speed)
        if wind_speed > wind_speed_max:
            result['wind_speed'] = wind_speed_max
            logging.debug('Wind speed {} should not exceed maximum wind speed {}'.format(wind_speed, wind_speed_max))

        return result


class Display(object):
    def __init__(self, interface, **configuration):
        self.wv_interface = interface
        self.enabled = configuration.get('auto-turn-off', False)
        start_time = configuration.get('start-time', '6:30')
        self.start_at_minutes = self.__convert_to_elapsed_minutes__(start_time)
        end_time = configuration.get('end-time', '22:00')
        self.end_at_minutes = self.__convert_to_elapsed_minutes__(end_time)
        self.pin = configuration.get('pin', 4)
        
    def __convert_to_elapsed_minutes__(time_text):
        time_array = [int(time_element) for time_element in time_text.split(':')]
        minutes = time_array[0] * 60
        minutes += time_array[1]
        return minutes
    
    def is_active(current_minute, start_time, end_time):
        if start_time < end_time:
            return self.start_at_minutes < current_minute < self.end_at_minutes
        else:
            return self.end_at_minutes < current_minute < self.start_at_minutes
    
    def tick(self):
        if self.enabled:
            t = time.localtime()
            current_minute = (t.tm_hour * 60) + t.tm_min
            if self.is_active(current_minute, self.start_at_minutes, self.end_at_minutes):
                self.wv_interface.gpio.write_pin(self.pin, 1)
            else:
                self.wv_interface.gpio.write_pin(self.pin, 0)
        else:
            pass
