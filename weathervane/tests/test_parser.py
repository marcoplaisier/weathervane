import csv
import os
import unittest
from weathervane import parser
from weathervane.parser import BuienradarParser


class test_parser(unittest.TestCase):
    def setUp(self):
        with file(os.path.join(os.getcwd(), 'weathervane', 'tests', 'buienradar.xml'), 'rU') as f:
            data = f.read()
            self.p = BuienradarParser(data)

    def wind_speed_parse_test(self):
        wind_speed = float(self.p.get_wind_speed(6391))
        assert wind_speed == 4.72

    def temperature_test(self):
        temperature = float(self.p.get_temperature(6275))
        assert temperature == 16.4

    def wind_chill_parse_test(self):
        wind_chill = float(self.p.get_wind_chill(6391))
        self.assertAlmostEqual(15.8, wind_chill, 1)

    def station_codes_test(self):
        station_codes = self.p.get_station_codes()
        expected_codes = [6275, 6391, 6249, 6308, 6260, 6235, 6370, 6377, 6321, 6350, 6283, 6280, 6315, 6278, 6356,
                          6330, 6311, 6279, 6251, 6258, 6285, 6209, 6225, 6210, 6277, 6320, 6270, 6269, 6348, 6380,
                          6273, 6286, 6312, 6344, 6343, 6316, 6240, 6324, 6267, 6331, 6290, 6313, 6242, 6310, 6375,
                          6215, 6319, 6248, 6257, 6340, 6239, 6252]
        assert station_codes.sort() == expected_codes.sort()


def wind_chill_test():
    with file(os.path.join(os.getcwd(), 'weathervane', 'tests', 'testdata.csv'), 'rU') as f:
        data = csv.DictReader(f)
        for line in data:
            wind_speed = float(line['windspeed'])
            temperature = float(line['temperature'])
            expected_wind_chill = float(line['wind chill'])
            yield check_wind_chill, wind_speed, temperature, expected_wind_chill, 0


def check_wind_chill(wind_speed, temperature, expected, places):
    calculated_wind_chill = parser.get_wind_chill(wind_speed, temperature)
    assert round(abs(expected - calculated_wind_chill), places) == 0
