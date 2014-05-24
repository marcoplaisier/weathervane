from mock import patch
import unittest
from weathervane.weathervaneinterface import WeatherVaneInterface


@patch('weathervane.weathervaneinterface.GPIO', autospec=True)
class WeatherVaneTest(unittest.TestCase):
    def test_init(self, mock_class):
        result = WeatherVaneInterface()
        expected = 'WeatherVaneInterface(channel=0, frequency=250000)'
        self.assertEqual(expected, str(result), 'Weather Vane Interface failed to be setup correctly - %s, %s'
                                                % (expected, result))

    def test_toggle_bit_empty_data(self, mock_class):
        interface = WeatherVaneInterface()
        self.assertFalse(interface.data_changed)
        interface.send({})
        self.assertFalse(interface.data_changed)

    def test_toggle_bit_toggled(self, mock_class):
        interface = WeatherVaneInterface()
        interface.send({'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})
        self.assertTrue(interface.data_changed)
        interface.send({'wind_direction': 'N', 'wind_speed': 0, 'air_pressure': 900})
        self.assertTrue(interface.data_changed)

    def test_toggle_bit_non_toggled(self, mock_class):
        interface = WeatherVaneInterface()
        interface._WeatherVaneInterface__get_data_changed(
            {'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 100})
        result = interface._WeatherVaneInterface__get_data_changed(
            {'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})
        expected = 128
        self.assertEqual(result, expected)

    def test_integer(self, mock_class):
        interface = WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, 3)

    def test_non_iterable(self, mock_class):
        interface = WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, None)

    def test_only_air_pressure(self, mock_class):
        interface = WeatherVaneInterface()
        expected = [0x00, 0x00, 0x00, 0x00, 0b11011011, 0x00]
        result = interface._WeatherVaneInterface__convert_data({'air_pressure': 900})
        self.assertEqual(expected, result)

    def test_error_wind_direction(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0
        result, errors = interface._WeatherVaneInterface__cast_wind_direction_to_byte({'wind_direction': 'A'})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000001, errors)

    def test_air_pressure(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 1
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte({'air_pressure': 901})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_air_pressure_too_low(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte({'air_pressure': 899})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000100, errors)

    def test_air_pressure_too_high(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 1155 - 900
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte({'air_pressure': 1156})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000100, errors)

    def test_air_pressure_rounded(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 100
        result, errors = interface._WeatherVaneInterface__cast_air_pressure_to_byte({'air_pressure': 1000.495})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_too_high(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 63
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte({'wind_speed': 64})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000010, errors)

    def test_wind_speed(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 10
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte({'wind_speed': 10})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_rounded(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 10
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte({'wind_speed': 9.99})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_too_low(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0x00
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_to_byte({'wind_speed': -1})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000010, errors)

    def test_wind_speed_max(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0x01
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte({'wind_speed_max': 1})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_speed_max_too_low(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0x00
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte({'wind_speed_max': -1})
        self.assertEqual(expected, result)
        self.assertEqual(0b00001000, errors)

    def test_wind_speed_max_too_high(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 63
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte({'wind_speed_max': 64})
        self.assertEqual(expected, result)
        self.assertEqual(0b00001000, errors)

    def test_wind_speed_rounded(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 50
        result, errors = interface._WeatherVaneInterface__cast_wind_speed_max_to_byte({'wind_speed_max': 50.394})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_direction(self, mock_class):
        interface = WeatherVaneInterface()
        expected = 0x0D
        result, errors = interface._WeatherVaneInterface__cast_wind_direction_to_byte({'wind_direction': 'WNW'})
        self.assertEqual(expected, result)
        self.assertEqual(0b00000000, errors)

    def test_wind_direction_not_present(self, mock_class):
        interface = WeatherVaneInterface()
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010001, 0x00]
        result = interface._WeatherVaneInterface__convert_data({'air_pressure': 900, 'wind_speed_max': 0,
                                                                'wind_speed': 0})
        self.assertEqual(expected, result)

    def test_air_pressure_not_present(self, mock_class):
        interface = WeatherVaneInterface()
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010100, 0x00]
        result = interface._WeatherVaneInterface__convert_data({'wind_direction': 'N', 'wind_speed_max': 0,
                                                                'wind_speed': 0})
        self.assertEqual(expected, result)

    def test_wind_speed_not_present(self, mock_class):
        interface = WeatherVaneInterface()
        expected = [0x00, 0x00, 0x00, 0x00, 0b11010010, 0x00]
        result = interface._WeatherVaneInterface__convert_data({'wind_direction': 'N', 'wind_speed_max': 0,
                                                                'air_pressure': 900})
        self.assertEqual(expected, result)


if __name__ == '__main__':
    unittest.main()
