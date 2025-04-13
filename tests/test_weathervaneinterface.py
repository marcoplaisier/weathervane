import unittest
from unittest.mock import patch

from tests import test_config
from weathervane.weathervaneinterface import WeatherVaneInterface


@patch("weathervane.weathervaneinterface.GPIO", autospec=True)
class WeatherVaneTest(unittest.TestCase):
    @patch("weathervane.weathervaneinterface.GPIO", autospec=True)
    def setUp(self, mock_class):
        self.interface = WeatherVaneInterface(**test_config.config)

    def noArguments(self, mock_class):
        self.assertRaises(KeyError, WeatherVaneInterface)

    def test_init(self, mock_class):
        result = WeatherVaneInterface(**test_config.config)
        expected = "WeatherVaneInterface(channel=0, frequency=250000)"
        self.assertEqual(
            expected,
            str(result),
            "Weather Vane Interface failed to be setup correctly - %s, %s"
            % (expected, result),
        )

    def test_transmittable_data_length(self, mock_class):
        weather_data = {"winddirection": "NO"}
        self.interface.send(weather_data)

    def test_transmittable_data_length_2(self, mock_class):
        weather_data = {
            "winddirection": "NO",
            "windspeed": 10,
            "windgusts": 15,
            "windspeedBft": 6,
            "airpressure": 1014,
            "temperature": 20,
            "feeltemperature": 21,
            "humidity": 100,
        }
        self.interface.send(weather_data)

    def test_error_winddirection(self, mock_class):
        weather_data = {"winddirection": "A"}
        requested_data = [{"key": "winddirection", "length": "4"}]
        expected = {"winddirection": 0}
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_air_pressure(self, mock_class):
        weather_data = {"airpressure": 901}
        requested_data = [
            {
                "key": "airpressure",
                "length": "8",
                "max": "1155",
                "min": "900",
                "step": "1",
            }
        ]
        expected = {"airpressure": 1}
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_rounded(self, mock_class):
        weather_data = {"airpressure": 48.493}
        requested_data = [{"key": "airpressure", "min": "0", "max": 63}]
        expected = {"airpressure": 48}
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_too_low(self, mock_class):
        weather_data = {"windspeed": -1}
        requested_data = [{"key": "windspeed", "min": "0", "max": 63}]
        expected = {"windspeed": 0}
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_too_high(self, mock_class):
        weather_data = {"windspeed": 64}
        requested_data = [{"key": "windspeed", "min": "0", "max": 63}]
        expected = {"windspeed": 63}
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_winddirection(self, mock_class):
        weather_data = {"winddirection": "WNW"}
        expected = {"winddirection": 0x0D}
        requested_data = [{"key": "winddirection", "length": 4}]
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_windspeed_may_not_exceed_windgusts(self, mock_class):
        windspeed = 10
        weather_data = {"windspeed": windspeed + 1, "windgusts": windspeed}
        expected = {"windspeed": windspeed, "windgusts": windspeed}
        requested_data = [
            {"key": "windspeed", "min": 0, "step": 1, "max": 63, "length": 8},
            {"key": "windgusts", "min": 0, "step": 1, "max": 63, "length": 8},
        ]
        result = self.interface._transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
