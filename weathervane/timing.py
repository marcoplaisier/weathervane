from interfaces.weathervaneinterface import WeatherVaneInterface
from mock import patch
import unittest

@patch('interfaces.weatherinterface.spi')
class TimingTest(unittest.TestCase):
    def __init__():
        self.wvi = WeatherVaneInterface()
    
    def t_test(self, mock_class):
        before = datetime.now()
        self.wvi.send({'wind_direction': 'NNO', 'wind_speed': 0, 'air_pressure': 900})
        after = datetime.now()
        print after-now

if __name__ == '__main__':
    unittest.main()
