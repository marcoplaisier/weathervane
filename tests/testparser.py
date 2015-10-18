import csv
import os
import unittest

from weathervane.parser import BuienradarParser


class testParser(unittest.TestCase):
    def setUp(self):
        with file(os.path.join(os.getcwd(), 'buienradar.xml'), 'rU') as f:
            data = f.read()
            config = {
                'stations': {
                    'pins': [0, 1],
                    'config': {0: 6275,
                               1: 2}
                },
                'bits': {
                    '0': {'key': 'wind_direction'},
                    '1': {'key': 'wind_speed'},
                    '2': {'key': 'wind_speed_max'},
                    '3': {'key': 'wind_speed_bft'},
                    '4': {'key': 'air_pressure'},
                    '5': {'key': 'temperature'},
                    '6': {'key': 'wind_chill'},
                    '7': {'key': 'humidity'},
                    '8': {'key': 'station_name'},
                    '9': {'key': 'latitude'},
                    '10': {'key': 'longitude'},
                    '11': {'key': 'date'},
                    '12': {'key': 'wind_direction_code'},
                    '13': {'key': 'sight_distance'},
                    '14': {'key': 'rain_mm_per_hour'},
                    '15': {'key': 'temperature_10_cm'},
                    '16': {'key': 'trend'}
                }
            }
            bp = BuienradarParser()
            self.weather_data = bp.parse(data, 6275, **config)
            print self.weather_data

    def wind_speed_parse_test(self):
        wind_speed = self.weather_data['wind_speed']
        assert wind_speed == 5.01

    def temperature_test(self):
        temperature = self.weather_data['temperature']
        assert temperature == 15.2

    def wind_chill_parse_test(self):
        wind_chill = self.weather_data['wind_chill']
        self.assertAlmostEqual(14.0, wind_chill, 1)

    def station_codes_test(self):
        with file(os.path.join(os.getcwd(), 'tests', 'buienradar.xml'), 'rU') as f:
            data = f.read()
            bp = BuienradarParser()
            station_codes = bp.station_codes(data)
            expected_codes = [6275, 6391, 6249, 6308, 6260, 6235, 6370, 6377, 6321, 6350, 6283, 6280, 6315, 6278, 6356,
                              6330, 6311, 6279, 6251, 6258, 6285, 6209, 6225, 6210, 6277, 6320, 6270, 6269, 6348, 6380,
                              6273, 6286, 6312, 6344, 6343, 6316, 6240, 6324, 6267, 6331, 6290, 6313, 6242, 6310, 6375,
                              6215, 6319, 6248, 6257, 6340, 6239, 6252]
            assert station_codes.sort() == expected_codes.sort()

    def test_trend(self):
        bp = BuienradarParser()
        bp.historic_data = [1000, 1000]
        with file(os.path.join(os.getcwd(), 'buienradar.xml'), 'rU') as f:
            data = f.read()
            config = {
                'stations': {
                    'pins': [0, 1],
                    'config': {0: 6275,
                               1: 2,
                               3: 6260}
                },
                'trend': 'air_pressure',
                'bits': {
                    '0': {'key': 'wind_direction'},
                    '1': {'key': 'wind_speed'},
                    '2': {'key': 'wind_speed_max'},
                    '3': {'key': 'wind_speed_bft'},
                    '4': {'key': 'air_pressure'},
                    '5': {'key': 'temperature'},
                    '6': {'key': 'wind_chill'},
                    '7': {'key': 'humidity'},
                    '8': {'key': 'station_name'},
                    '9': {'key': 'latitude'},
                    '10': {'key': 'longitude'},
                    '11': {'key': 'date'},
                    '12': {'key': 'wind_direction_code'},
                    '13': {'key': 'sight_distance'},
                    '14': {'key': 'rain_mm_per_hour'},
                    '15': {'key': 'temperature_10_cm'},
                    '16': {'key': 'trend'}
                }
            }
            weather_data = bp.parse(data, 6260, **config)
        self.assertEqual(1, weather_data['trend'])

def wind_chill_test():
    with file(os.path.join(os.getcwd(), 'tests', 'testdata.csv'), 'rU') as f:
        data = csv.DictReader(f)
        for line in data:
            wind_speed = float(line['windspeed'])
            temperature = float(line['temperature'])
            expected_wind_chill = float(line['wind chill'])
            yield check_wind_chill, wind_speed, temperature, expected_wind_chill, 0


def check_wind_chill(wind_speed, temperature, expected, places):
    calculated_wind_chill = BuienradarParser.calculate_wind_chill(wind_speed, temperature)
    assert round(abs(expected - calculated_wind_chill), places) == 0
