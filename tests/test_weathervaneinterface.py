import unittest
from unittest.mock import patch

from tests import test_config
from weathervane.weathervaneinterface import WeatherVaneInterface, Display


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
        
    @patch("weathervane.weathervaneinterface.gpiozero.LED")
    def test_display_is_active(self, mock_led, mock_class):
        """Test that Display.is_active() correctly handles both normal and overnight times."""
        # Normal time range (e.g., 6:30 to 22:00)
        display = Display(
            **{"auto-turn-off": True, "start-time": "06:30", "end-time": "22:00", "pin": 4}
        )
        
        # Test times within normal range
        self.assertTrue(display.is_active(display.convert_to_minutes("06:30")))  # Start time
        self.assertTrue(display.is_active(display.convert_to_minutes("12:00")))  # Mid-day
        self.assertTrue(display.is_active(display.convert_to_minutes("22:00")))  # End time
        
        # Test times outside normal range
        self.assertFalse(display.is_active(display.convert_to_minutes("06:29")))  # Just before start
        self.assertFalse(display.is_active(display.convert_to_minutes("22:01")))  # Just after end
        self.assertFalse(display.is_active(display.convert_to_minutes("00:00")))  # Midnight
        
        # Overnight time range (e.g., 22:00 to 06:30)
        overnight_display = Display(
            **{"auto-turn-off": True, "start-time": "22:00", "end-time": "06:30", "pin": 4}
        )
        
        # Test times within overnight range
        self.assertTrue(overnight_display.is_active(overnight_display.convert_to_minutes("22:00")))  # Start time
        self.assertTrue(overnight_display.is_active(overnight_display.convert_to_minutes("00:00")))  # Midnight
        self.assertTrue(overnight_display.is_active(overnight_display.convert_to_minutes("06:30")))  # End time
        
        # Test times outside overnight range
        self.assertFalse(overnight_display.is_active(overnight_display.convert_to_minutes("21:59")))  # Just before start
        self.assertFalse(overnight_display.is_active(overnight_display.convert_to_minutes("06:31")))  # Just after end
        self.assertFalse(overnight_display.is_active(overnight_display.convert_to_minutes("12:00")))  # Mid-day

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
