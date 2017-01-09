import csv
import os
import unittest
from datetime import datetime

from weathervane.parser import BuienradarParser
from weathervane.weather import Weather


class testParser(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(os.getcwd(), 'tests', 'buienradar.xml'), 'rU') as f:
            data = f.read()
            config = {
                'stations':
                    {0: 6275,
                     1: 6203},
                'bits': {
                    '0': {'key': 'wind_direction'},
                    '1': {'key': 'wind_speed'},
                    '2': {'key': 'wind_speed_max'},
                    '3': {'key': 'wind_speed_bft'},
                    '4': {'key': 'air_pressure'},
                    '5': {'key': 'temperature'},
                    '6': {'key': 'apparent_temperature'},
                    '7': {'key': 'humidity'},
                    '8': {'key': 'station_name'},
                    '9': {'key': 'latitude'},
                    '10': {'key': 'longitude'},
                    '11': {'key': 'date'},
                    '12': {'key': 'wind_direction_code'},
                    '13': {'key': 'sight_distance'},
                    '14': {'key': 'rain'},
                    '15': {'key': 'temperature_10_cm'},
                    '16': {'key': 'barometric_trend'},
                    '17': {'key': 'data_from_fallback'}
                }
            }
            bp = BuienradarParser(**config)
            bp.historic_data = {
                datetime(2015, 5, 14, 13, 50, 00): 1000
            }
            self.weather_data = bp.parse(raw_xml=data, **config)

    def test_wind_speed_parse(self):
        wind_speed = self.weather_data['wind_speed']
        assert wind_speed == 5.01

    def test_temperature(self):
        temperature = self.weather_data['temperature']
        assert temperature == 15.2

    def test_apparent_temperature_parse(self):
        apparent_temperature = self.weather_data['apparent_temperature']
        self.assertAlmostEqual(15.2, apparent_temperature, 0)

    def test_barometric_trend(self):
        self.assertEqual(1, self.weather_data['barometric_trend'])

    def test_wind_chill(self):
        with open(os.path.join(os.getcwd(), 'tests', 'testdata_windchill.csv'), 'rU') as f:
            data = csv.DictReader(f)
            for line in data:
                wind_speed = float(line['windspeed'])
                temperature = float(line['temperature'])
                expected_apparent_temperature = float(line['wind chill'])
                assert Weather.wind_chill(wind_speed, temperature) == expected_apparent_temperature

