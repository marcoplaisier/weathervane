from mock import patch
from interfaces.weathervaneinterface import WeatherVaneInterface
import unittest

#noinspection PyUnusedLocal,PyUnusedLocal,PyUnusedLocal,PyUnusedLocal,PyUnusedLocal,PyUnusedLocal
@patch('interfaces.weathervaneinterface.spi', autospec=True)
class WeatherVaneTest(unittest.TestCase):

    def test_init(self, mock_class):
        result = WeatherVaneInterface()
        expected = 'WeatherVaneInterface(channel=0, frequency=50000)'
        self.assertEqual(expected, str(result), 'Weather Vane Interface failed to be setup correctly - %s, %s'
                                                 %(expected, result))

    def test_send_data(self, mock_class):
        interface = WeatherVaneInterface()
        interface.send({'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})

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
        interface.send({'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})
        self.assertTrue(interface.data_changed)
        interface.send({'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})
        self.assertFalse(interface.data_changed)

    def test_integer(self, mock_class):
        interface =  WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, 3)

    def test_non_iterable(self, mock_class):
        interface =  WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, None)

if __name__ == '__main__':
    unittest.main()
