import unittest

from unittest.mock import Mock, patch

from weathervane.weathervaneinterface import WeatherVaneInterface
from tests import test_config


@patch('weathervane.weathervaneinterface.GPIO', autospec=True)
class WeatherVaneTest(unittest.TestCase):
    @patch('weathervane.weathervaneinterface.GPIO', autospec=True)
    def setUp(self, mock_class):
        self.interface = WeatherVaneInterface(**test_config.config)

    def noArguments(self, mock_class):
        self.assertRaises(KeyError, WeatherVaneInterface)

    def test_init(self, mock_class):
        result = WeatherVaneInterface(**test_config.config)
        expected = 'WeatherVaneInterface(channel=0, frequency=250000)'
        self.assertEqual(expected, str(result), 'Weather Vane Interface failed to be setup correctly - %s, %s'
                         % (expected, result))

    def test_bitstring_length(self, mock_class):
        weather_data = {'wind_direction': 'NO'}
        self.interface.send(weather_data)
        self.assertEqual(len(self.interface.new_bit_string), 64)

    def test_toggle_bit_empty_data(self, mock_class):
        weather_data = {'wind_direction': 'NO'}
        self.assertFalse(self.interface.data_changed)
        self.interface.send(weather_data)
        self.assertTrue(self.interface.data_changed)

    def test_bitstring_length_2(self, mock_class):
        weather_data = {'wind_direction': 'NO',
                        'wind_speed': 10,
                        'wind_speed_max': 15,
                        'wind_speed_bft': 6,
                        'air_pressure': 1014,
                        'temperature': 20,
                        'apparent_temperature': 21,
                        'humidity': 100}
        self.interface.send(weather_data)
        self.assertEqual(len(self.interface.new_bit_string), 64)

    def test_toggle_bit(self, mock_class):
        weather_data = {'wind_direction': 'NO',
                        'wind_speed': 0,
                        'wind_speed_max': 0,
                        'wind_speed_bft': 1,
                        'air_pressure': 900,
                        'temperature': 20,
                        'apparent_temperature': 21,
                        'humidity': 100}
        self.interface.send(weather_data)
        self.assertTrue(self.interface.data_changed)

        weather_data = {'wind_direction': 'O',
                        'wind_speed': 0,
                        'wind_speed_max': 0,
                        'wind_speed_bft': 1,
                        'air_pressure': 900,
                        'temperature': 20,
                        'apparent_temperature': 21,
                        'humidity': 100}

        self.interface.send(weather_data)
        self.assertTrue(self.interface.data_changed)

        self.interface.send(weather_data)
        self.assertFalse(self.interface.data_changed)

    def test_error_wind_direction(self, mock_class):
        weather_data = {'wind_direction': 'A'}
        requested_data = {'0': {'key': 'wind_direction', 'length': '4'}}
        expected = {'wind_direction': 0}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_air_pressure(self, mock_class):
        weather_data = {'air_pressure': 901}
        requested_data = {'1': {'key': 'air_pressure', 'length': '8', 'max': '1155', 'min': '900', 'step': '1'}}
        expected = {'air_pressure': 1}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_rounded(self, mock_class):
        weather_data = {'air_pressure': 48.493}
        requested_data = {'0': {'key': 'air_pressure', 'min': '0', 'max': 63}}
        expected = {'air_pressure': 48}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_too_low(self, mock_class):
        weather_data = {'wind_speed': -1}
        requested_data = {'0': {'key': 'wind_speed', 'min': '0', 'max': 63}}
        expected = {'wind_speed': 0}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_value_too_high(self, mock_class):
        weather_data = {'wind_speed': 64}
        requested_data = {'0': {'key': 'wind_speed', 'min': '0', 'max': 63}}
        expected = {'wind_speed': 63}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_wind_direction(self, mock_class):
        weather_data = {'wind_direction': 'WNW'}
        expected = {'wind_direction': 0x0D}
        requested_data = {'0': {'key': 'wind_direction', 'length': 4}}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)

    def test_wind_speed_may_not_exceed_wind_speed_max(self, mock_class):
        wind_speed = 10
        weather_data = {'wind_speed': wind_speed + 1, 'wind_speed_max': wind_speed}
        expected = {'wind_speed': wind_speed, 'wind_speed_max': wind_speed}
        requested_data = {'0': {'key': 'wind_speed', 'min': 0, 'step': 1, 'max': 63, 'length': 8},
                          '1': {'key': 'wind_speed_max', 'min': 0, 'step': 1, 'max': 63, 'length': 8}}
        result = self.interface.transmittable_data(weather_data, requested_data)
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
