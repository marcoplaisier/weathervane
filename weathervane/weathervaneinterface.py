import logging
import math
import time
from random import randint
from typing import List, Dict, Any, Union, Optional

import gpiozero

from weathervane.gpio import GPIO

logger = logging.getLogger()


class WeatherVaneInterface(object):
    wind_directions: Dict[str, int] = {
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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.channel: int = kwargs["channel"]
        self.frequency: int = kwargs["frequency"]
        self.gpio: GPIO = GPIO(**kwargs)
        self.bits: List[Dict[str, Any]] = kwargs["bits"]
        self.stations: List[int] = kwargs["stations"]

    def __repr__(self) -> str:
        return "WeatherVaneInterface(channel=%d, frequency=%d)" % (
            self.channel,
            self.frequency,
        )

    def encode_weather_data(self, weather_data: Dict[str, Any]) -> bytes:
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
        @return: a byte array
        """
        t_data = self._transmittable_data(weather_data, self.bits)

        binary_string = ""
        for data in self.bits:
            bit_key = data["key"]
            bit_value = f"{t_data[bit_key]:0{int(data['length'])}b}"
            binary_string += bit_value
        data_length = math.ceil(len(binary_string) / 8)
        binary_string_list_in_bytes = [binary_string[i * 8:(i * 8) + 8] for i in range(data_length)]
        data_bytes = bytearray([int(b, base=2) for b in binary_string_list_in_bytes])
        return data_bytes

    def send(self, weather_data: Dict[str, Any]) -> None:
        """Send data to the connected SPI device.

        Keyword arguments:
        weather_data -- a dictionary with the data
        """
        data_array = self.encode_weather_data(weather_data)
        logger.info(f'Sending data {data_array} to device')
        self.gpio.send_data(data_array)


    def _transmittable_data(self, weather_data: Dict[str, Any], requested_data: List[Dict[str, Any]]) -> Dict[str, int]:
        result: Dict[str, int] = {}

        for data_point in requested_data:
            measurement_name = data_point["key"]
            value = weather_data.get(measurement_name, 0)
            if measurement_name == "random":
                length = int(data_point["length"])
                value = randint(0, 2 ** length - 1)

            step_value = float(data_point.get("step", 1))
            min_value = float(data_point.get("min", 0))
            max_value = float(data_point.get("max", 255))
            result[measurement_name] = self._value_to_bits(
                measurement_name, value, step_value, min_value, max_value
            )
            result = WeatherVaneInterface._compensate_wind(result)

        return result

    def _value_to_bits(self, measurement_name: str, value: Any, step_value: float, min_value: float, max_value: float) -> int:
        if measurement_name == "winddirection":
            return self.wind_directions.get(value, 0)
        elif measurement_name == "precipitation":
            return 1 if value and value > 0 else 0
        else:
            if not value:
                logger.debug("Value {} is missing. Setting to min-value".format(value))
            value = min(max(value, min_value), max_value)

            try:
                value -= min_value
                value /= float(step_value)
            except TypeError:
                logger.debug(
                    "Value {} for {} is not a number".format(value, measurement_name)
                )
                return 0

            return int(value)

    @staticmethod
    def _compensate_wind(result: Dict[str, int]) -> Dict[str, int]:
        windspeed = result.get("windspeed", 0)
        windgusts = result.get("windgusts", windspeed)
        if windspeed > windgusts:
            result["windspeed"] = windgusts
            logger.debug(
                "Wind speed {} should not exceed maximum wind speed {}".format(
                    windspeed, windgusts
                )
            )

        return result


class Display(object):
    def __init__(self, **kwargs: Any) -> None:
        self.auto_disable_display: bool = kwargs.get("auto-turn-off", False)
        start_time: str = kwargs.get("start-time", "6:30")
        self.start_at_minutes: int = Display.convert_to_minutes(start_time)
        end_time: str = kwargs.get("end-time", "22:00")
        self.end_at_minutes: int = Display.convert_to_minutes(end_time)
        self.display: gpiozero.LED = gpiozero.LED(kwargs.get("pin", 4))

    @staticmethod
    def convert_to_minutes(time_text: str) -> int:
        time_array = [int(time_element) for time_element in time_text.split(":")]
        minutes = time_array[0] * 60
        minutes += time_array[1]
        return minutes

    def is_active(self, current_minute: int) -> bool:
        if self.start_at_minutes < self.end_at_minutes:
            # Normal case (e.g., 6:30 - 22:00)
            return self.start_at_minutes <= current_minute <= self.end_at_minutes
        else:
            # Overnight case (e.g., 22:00 - 6:30)
            return ((self.convert_to_minutes("00:00") <= current_minute <= self.end_at_minutes) or
                    (self.start_at_minutes <= current_minute <= self.convert_to_minutes("23:59")))

    async def tick(self) -> None:
        if self.auto_disable_display:
            time_text = time.strftime("%H:%M")
            current_minute = Display.convert_to_minutes(time_text)
            if self.is_active(current_minute):
                self.display.on()
            else:
                self.display.off()
