import csv
import os
import unittest
from weathervane import parser


def test_wind_chill():
    with file(os.path.join(os.getcwd(), 'testdata.csv'), 'rU') as f:
        data = csv.DictReader(f)
        for line in data:
            wind_speed = float(line['windspeed'])
            temperature = float(line['temperature'])
            expected_wind_chill = float(line['wind chill'])
            yield check_wind_chill, wind_speed, temperature, expected_wind_chill, 0


def check_wind_chill(wind_speed, temperature, expected, places):
    calculated_wind_chill = parser.get_wind_chill(wind_speed, temperature)
    assert round(abs(expected-calculated_wind_chill), places) == 0