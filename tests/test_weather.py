import unittest
from weathervane.weatherdata.weatherdata import WeatherData

class test_weather(unittest.TestCase):
    def test_init(self):
        testdata = {'windrichting': 'NNO', 'windsnelheid': 4.5}
        w = WeatherData(testdata)
        self.assertEquals(w.get('windrichting'), 'NNO')
        self.assertEquals(w.get('windsnelheid'), 4.5)
        
