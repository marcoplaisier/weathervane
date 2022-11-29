import logging
import time
from random import randint
from typing import List

import bitstring

from weathervane.gpio import GPIO


class WeatherVaneInterface(object):
    wind_directions = {
        "N": 0x00,
        "NNO": 0x01,
        "NO": 0x02,
        "ONO": 0x03,
        "O": 0x04,
        "OZO": 0x05,
        "ZO": 0x06,
        "ZZO": 0x07,
        "Z": 0x08,
        "ZZW": 0x09,
        "ZW": 0x0A,
        "WZW": 0x0B,
        "W": 0x0C,
        "WNW": 0x0D,
        "NW": 0x0E,
        "NNW": 0x0F,
    }

    def __init__(self, *args, **kwargs):
        self.channel = kwargs["channel"]
        self.frequency = kwargs["frequency"]
        self.gpio = GPIO(**kwargs)
        self.old_bit_string = None
        self.new_bit_string = None
        self.weather_data = {}
        self.bits: List[dict] = kwargs["bits"]
        self.stations = kwargs["stations"]

    def __repr__(self):
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % (
            self.channel,
            self.frequency,
        )

    @property
    def data_changed(self):
        """Return whether or not the data was different the last time it was sent.

        @return: a boolean indicating whether the data has changed
        """
        return self.old_bit_string != self.new_bit_string

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
        t_data = self.transmittable_data(weather_data, self.bits)

        for i, data in enumerate(self.bits):
            formatting = self.bits[i]
            bit_length = int(formatting["length"])
            bit_key = formatting["key"]
            bit_value = t_data[bit_key]
            padding_string = "#0{0}b".format(
                bit_length + 2
            )  # account for '0b' in the length
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

    def transmittable_data(self, weather_data, requested_data: List[dict]):
        result = {}

        for data_point in requested_data:
            measurement_name = data_point["key"]
            value = weather_data.get(measurement_name, 0)
            if measurement_name == "random":
                length = int(data_point["length"])
                value = randint(0, 2**length - 1)

            step_value = float(data_point.get("step", 1))
            min_value = float(data_point.get("min", 0))
            max_value = float(data_point.get("max", 255))
            result[measurement_name] = self.value_to_bits(
                measurement_name, value, step_value, min_value, max_value
            )
            result = self.compensate_wind(result)

        return result

    def value_to_bits(self, measurement_name, value, step_value, min_value, max_value):
        if measurement_name == "winddirection":
            return self.wind_directions.get(value, 0)
        elif measurement_name == "precipitation":
            return 1 if value and value > 0 else 0
        else:
            if not value:
                logging.debug("Value {} is missing. Setting to min-value".format(value))
            value = min(max(value, min_value), max_value)

            try:
                value -= min_value
                value /= float(step_value)
            except TypeError:
                logging.debug(
                    "Value {} for {} is not a number".format(value, measurement_name)
                )
                return 0

            return int(value)

    def compensate_wind(self, result):
        windspeed = result.get("windspeed", 0)
        windgusts = result.get("windgusts", windspeed)
        if windspeed > windgusts:
            result["windspeed"] = windgusts
            logging.debug(
                "Wind speed {} should not exceed maximum wind speed {}".format(
                    windspeed, windgusts
                )
            )

        return result


class Display(object):
    def __init__(self, interface, **configuration):
        self.wv_interface = interface
        self.auto_disable_display = configuration.get("auto-turn-off", False)
        start_time = configuration.get("start-time", "6:30")
        self.start_at_minutes = Display.convert_to_minutes(start_time)
        end_time = configuration.get("end-time", "22:00")
        self.end_at_minutes = Display.convert_to_minutes(end_time)
        self.pin = configuration.get("pin", 4)

    @staticmethod
    def convert_to_minutes(time_text):
        time_array = [int(time_element) for time_element in time_text.split(":")]
        minutes = time_array[0] * 60
        minutes += time_array[1]
        return minutes

    def is_active(self, current_minute):
        if self.start_at_minutes < self.end_at_minutes:
            return self.start_at_minutes < current_minute < self.end_at_minutes
        else:
            return self.end_at_minutes < current_minute < self.start_at_minutes

    def tick(self):
        if self.auto_disable_display:
            time_text = time.strftime("%H:%M")
            current_minute = Display.convert_to_minutes(time_text)
            if self.is_active(current_minute):
                self.wv_interface.gpio.write_pin(self.pin, 1)
            else:
                self.wv_interface.gpio.write_pin(self.pin, 0)
