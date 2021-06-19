import csv
import os
import unittest
from datetime import datetime

from weathervane.parser import BuienradarParser


class testParser(unittest.TestCase):
    def setUp(self):
        file_path = os.path.join(os.getcwd(), 'tests', 'buienradar.json')
        with open(file_path, 'r', encoding='UTF-8') as f:
            data = f.read()
            config = {
                'stations': [6275, 6203],
                'bits': {
                    '0': {'key': 'wind_direction'},
                    '1': {'key': 'wind_speed'},
                    '2': {'key': 'wind_speed_max'},
                    '3': {'key': 'wind_speed_bft'},
                    '4': {'key': 'air_pressure'},
                    '5': {'key': 'temperature'},
                    '6': {'key': 'feeltemperature'},
                    '7': {'key': 'humidity'},
                    '8': {'key': 'station_name'},
                    '9': {'key': 'latitude'},
                    '10': {'key': 'longitude'},
                    '11': {'key': 'date'},
                    '12': {'key': 'wind_direction_code'},
                    '13': {'key': 'sight_distance'},
                    '14': {'key': 'precipitation'},
                    '15': {'key': 'temperature_10_cm'},
                    '16': {'key': 'barometric_trend'},
                    '17': {'key': 'data_from_fallback'}
                }
            }
            bp = BuienradarParser(**config)
            self.weather_data = bp.parse(data=data)

    def test_wind_speed_parse(self):
        wind_speed = self.weather_data['windspeed']
        assert wind_speed == 3.3

    def test_rain_parse(self):
        rain = self.weather_data['precipitation']
        assert rain == 45.2

    def test_temperature(self):
        temperature = self.weather_data['temperature']
        assert temperature == 20.2

    def test_feeltemperature(self):
        apparent_temperature = self.weather_data['feeltemperature']
        self.assertAlmostEqual(20, apparent_temperature, 0)

