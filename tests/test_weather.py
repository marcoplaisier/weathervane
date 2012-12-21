import unittest
from weathervane.weather.weather import Weather

class test_weather(unittest.TestCase):
    def test_init(self):
        testdata = {'windrichting': 'NNO', 'windsnelheid': 4.5}
        w = Weather(testdata)
        self.assertEquals(w.get('windrichting'), 'NNO')
        self.assertEquals(w.get('windsnelheid'), 4.5)
        
