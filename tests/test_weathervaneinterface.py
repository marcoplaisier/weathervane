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
        interface.send([1])

    def test_toggle_bit_empty_data(self, mock_class):
        interface = WeatherVaneInterface()
        self.assertIsNone(interface.data_changed)
        interface.send([])
        self.assertFalse(interface.data_changed)

    def test_toggle_bit_toggled(self, mock_class):
        interface = WeatherVaneInterface()
        interface.send([1])
        self.assertTrue(interface.data_changed)
        interface.send([2])
        self.assertTrue(interface.data_changed)

    def test_toggle_bit_non_toggled(self, mock_class):
        interface = WeatherVaneInterface()
        interface.send([1])
        self.assertTrue(interface.data_changed)
        interface.send([1])
        self.assertFalse(interface.data_changed)

    def test_integer(self, mock_class):
        interface =  WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, 3)

    def test_non_iterable(self, mock_class):
        interface =  WeatherVaneInterface()
        self.assertRaises(TypeError, interface.send, None)

    def test_immutable(self, mock_class):
        interface =  WeatherVaneInterface()
        try:
            interface.send((3, 4))
        except TypeError:
            self.fail("send() raised an exception on an immutable sequence")

if __name__ == '__main__':
    unittest.main()
