import unittest
from unittest.mock import patch

from tests import test_config
from weathervane.weathervaneinterface import WeatherVaneInterface


@patch("weathervane.weathervaneinterface.GPIO", autospec=True)
class TestEncodeWeatherData(unittest.TestCase):
    @patch("weathervane.weathervaneinterface.GPIO", autospec=True)
    def setUp(self, mock_class):
        self.interface = WeatherVaneInterface(**test_config.config)

    def test_returns_bytes(self, mock_class):
        weather_data = {
            "winddirection": "N",
            "windspeed": 0,
            "windgusts": 0,
            "windspeedBft": 1,
            "airpressure": 900,
            "temperature": -39.9,
            "feeltemperature": -39.9,
            "humidity": 0,
        }
        result = self.interface.encode_weather_data(weather_data)
        assert isinstance(result, (bytes, bytearray))

    def test_output_length_matches_config(self, mock_class):
        """Total bits from test_config: 4+6+6+4+8+10+10+7+5+4 = 64 bits = 8 bytes."""
        weather_data = {
            "winddirection": "N",
            "windspeed": 10,
            "windgusts": 15,
            "windspeedBft": 6,
            "airpressure": 1014,
            "temperature": 20.0,
            "feeltemperature": 21.0,
            "humidity": 50,
        }
        result = self.interface.encode_weather_data(weather_data)
        assert len(result) == 8

    def test_known_wind_direction_encoding(self, mock_class):
        """North = 0x00, so the first 4 bits should be 0000."""
        weather_data = {
            "winddirection": "N",
            "windspeed": 0,
            "windgusts": 0,
            "windspeedBft": 1,
            "airpressure": 900,
            "temperature": -39.9,
            "feeltemperature": -39.9,
            "humidity": 0,
        }
        result = self.interface.encode_weather_data(weather_data)
        # First nibble (4 bits) should be 0 for North
        first_nibble = (result[0] >> 4) & 0x0F
        assert first_nibble == 0x00

    def test_south_wind_direction_encoding(self, mock_class):
        """South = 0x08, first 4 bits should be 1000."""
        weather_data = {
            "winddirection": "Z",
            "windspeed": 0,
            "windgusts": 0,
            "windspeedBft": 1,
            "airpressure": 900,
            "temperature": -39.9,
            "feeltemperature": -39.9,
            "humidity": 0,
        }
        result = self.interface.encode_weather_data(weather_data)
        first_nibble = (result[0] >> 4) & 0x0F
        assert first_nibble == 0x08

    def test_different_data_produces_different_output(self, mock_class):
        base = {
            "winddirection": "N",
            "windspeed": 0,
            "windgusts": 0,
            "windspeedBft": 1,
            "airpressure": 900,
            "temperature": -39.9,
            "feeltemperature": -39.9,
            "humidity": 0,
        }
        warm = dict(base, temperature=30.0)
        result_cold = self.interface.encode_weather_data(base)
        result_warm = self.interface.encode_weather_data(warm)
        assert result_cold != result_warm


if __name__ == "__main__":
    unittest.main()
