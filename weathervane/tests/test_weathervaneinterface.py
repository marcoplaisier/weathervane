from mock import Mock, patch
import unittest
from weathervane.weathervaneinterface import WeatherVaneInterface
from weathervane.datasources import weather_data


@patch('weathervane.weathervaneinterface.GPIO', autospec=True)
class WeatherVaneTest(unittest.TestCase):
    @patch('weathervane.weathervaneinterface.GPIO', autospec=True)
    def setUp(self, mock_class):
        self.interface = WeatherVaneInterface(channel=0, frequency=0, stations={'pins': None, 'config': None})

    def test_init(self, mock_class):
        result = WeatherVaneInterface(channel=0, frequency=250000, stations={'pins': None, 'config': None})
        expected = 'WeatherVaneInterface(channel=0, frequency=250000)'
        self.assertEqual(expected, str(result), 'Weather Vane Interface failed to be setup correctly - %s, %s'
                         % (expected, result))

    def test_toggle_bit_empty_data(self, mock_class):
        interface = self.interface
        self.assertFalse(interface.data_changed)
        interface.send(weather_data(None, None, None, None))
        self.assertTrue(interface.data_changed)

    def test_toggle_bit_toggled(self, mock_class):
        interface = self.interface
        wd = weather_data(wind_direction='NNO', wind_speed=0, air_pressure=900, wind_speed_max=None)
        interface.send(wd)
        self.assertTrue(interface.data_changed)
        wd = weather_data(wind_direction='N', wind_speed=0, air_pressure=900, wind_speed_max=None)
        interface.send(wd)
        self.assertTrue(interface.data_changed)

    def test_toggle_bit_non_toggled(self, mock_class):
        interface = self.interface
        interface._WeatherVaneInterface__get_data_changed(
            weather_data(wind_direction='NNO', wind_speed=0, air_pressure=100, wind_speed_max=None))
        result = interface._WeatherVaneInterface__get_data_changed(
            weather_data(wind_direction='NNO', wind_speed=0, air_pressure=900, wind_speed_max=None))
        expected = 128
        self.assertEqual(result, expected)

    def test_only_air_pressure(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x00, 0x00, 0x00, 0b11011011, 0x00]
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=900)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_error_wind_direction(self, mock_class):
        interface = self.interface
        expected = 0
        wd = weather_data(wind_direction='A', wind_speed=None, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_direction_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000001, errors)

    def test_air_pressure(self, mock_class):
        interface = self.interface
        expected = 1
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=901)
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_air_pressure_too_low(self, mock_class):
        interface = self.interface
        expected = 0
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=899)
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000100, errors)

    def test_air_pressure_too_high(self, mock_class):
        interface = self.interface
        expected = 1155 - 900
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=1156)
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000100, errors)

    def test_air_pressure_rounded(self, mock_class):
        interface = self.interface
        expected = 100
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=1000.495)
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_too_high(self, mock_class):
        interface = self.interface
        expected = 63
        wd = weather_data(wind_direction=None, wind_speed=64, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000010, errors)

    def test_wind_speed(self, mock_class):
        interface = self.interface
        expected = 10
        wd = weather_data(wind_direction=None, wind_speed=10, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_rounded(self, mock_class):
        interface = self.interface
        expected = 10
        wd = weather_data(wind_direction=None, wind_speed=9.99, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_too_low(self, mock_class):
        interface = self.interface
        expected = 0x00
        wd = weather_data(wind_direction=None, wind_speed=-1, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000010, errors)

    def test_wind_speed_max(self, mock_class):
        interface = self.interface
        expected = 0x01
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=1, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_max_too_low(self, mock_class):
        interface = self.interface
        expected = 0x00
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=-1, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00001000, errors)

    def test_wind_speed_max_too_high(self, mock_class):
        interface = self.interface
        expected = 63
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=64, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00001000, errors)

    def test_wind_speed_rounded(self, mock_class):
        interface = self.interface
        expected = 50
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=50.394, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_direction(self, mock_class):
        interface = self.interface
        expected = 0x0D
        wd = weather_data(wind_direction='WNW', wind_speed=None, wind_speed_max=None, air_pressure=None)
        result, errors = interface._WeatherVaneInterface__cast_wind_direction_to_byte(wd)
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_direction_not_present(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010001, 0x00]
        wd = weather_data(wind_direction=None, wind_speed=0, wind_speed_max=0, air_pressure=900)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_air_pressure_not_present(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010100, 0x00]
        wd = weather_data(wind_direction='N', wind_speed=0, wind_speed_max=0, air_pressure=None)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_wind_speed_not_present(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010010, 0x00]
        wd = weather_data(wind_direction='N', wind_speed=None, wind_speed_max=0, air_pressure=900)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_wind_speed_may_not_exceed_wind_speed_max(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x01, 0x01, 0x00, 0b11010101, 0x00]
        wd = weather_data(wind_direction=None, wind_speed=1, wind_speed_max=0, air_pressure=None)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_wind_speed_must_be_equal_or_lower_than_wind_speed_max(self, mock_class):
        interface = self.interface
        expected = [0x00, 0x01, 0x02, 0x00, 0b11010101, 0x00]
        wd = weather_data(wind_direction=None, wind_speed=1, wind_speed_max=2, air_pressure=None)
        result = interface._WeatherVaneInterface__convert_data(wd)
        self.assertEqual(expected, result)

    def test_get_station(self, mock_class):
        config = {0: 6320, 1: 6321, 2: 6310, 3: 6312, 4: 6308, 5: 6311, 6: 6331, 7: 6316}
        interface = WeatherVaneInterface(channel=0, frequency=0, stations={'pins': [4, 5, 6], 'config': config})
        station_id = interface.selected_station
        self.assertEqual(station_id, 6320)

    def test_get_other_station(self, mock_class):
        config = {0: 6320, 1: 6321, 2: 6310, 3: 6312, 4: 6308, 5: 6311, 6: 6331, 7: 6316}
        interface = WeatherVaneInterface(channel=0, frequency=0, stations={'pins': [4, 5, 6], 'config': config})
        interface.gpio.read_pin = Mock(return_value=[1, 1, 0])
        station_id = interface.selected_station
        self.assertEqual(station_id, 6312)  # remember, byte ordering


if __name__ == '__main__':
    unittest.main()
