import datetime
import json
from pprint import pprint

import os
from behave import *

from weathervane.parser import BuienradarParser

use_step_matcher("re")


@then("usable weatherdata is returned")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assert context.result['wind_direction'] == "ONO"
    assert context.result['wind_speed'] == 5.01
    assert context.result['wind_speed_max'] == 8.2
    assert context.result['wind_speed_bft'] == 3
    assert context.result['air_pressure'] == 1011.560
    assert context.result['temperature'] == 15.2
    assert context.result['apparent_temperature'] == 15.2
    assert context.result['humidity'] == 47
    assert context.result['date'] == datetime.datetime(2015, 5, 14, 14, 16, 50)
    assert context.result['wind_direction_code'] == "ONO"
    assert context.result['sight_distance'] == 37000
    assert context.result['rain_mm_per_hour'] == 45.2
    assert context.result['temperature_10_cm'] == 18.0
    assert context.result['barometric_trend'] == 4
    assert context.result['data_from_fallback'] == False
    assert context.result['latitude'] == 52.04
    assert context.result['longitude'] == 5.53
    assert context.result['DUMMY_BYTE'] == None
    assert context.result['station_name'] == "Meetstation Arnhem"


@given("data from buienradar in json format")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    file_path = os.path.join(os.getcwd(), 'tests', 'buienradar.json')

    with open(file_path, 'r', encoding='utf-8') as f:
        data = f.read()
        context.weather_data_json = data


@when("the data is parsed")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    config = {'bits':
        {
            '0': {'key': 'wind_direction', 'length': '4'},
            '1': {'key': 'wind_speed', 'length': '6', 'max': '63', 'min': '0', 'step': '1'},
            '2': {'key': 'wind_speed_max', 'length': '6', 'max': '63', 'min': '0', 'step': '1'},
            '3': {'key': 'wind_speed_bft', 'length': '4', 'max': '12', 'min': '1', 'step': '1'},
            '4': {'key': 'air_pressure', 'length': '8', 'max': '1155', 'min': '900', 'step': '1'},
            '5': {'key': 'temperature', 'length': '10', 'max': '49.9', 'min': '-39.9', 'step': '0.1'},
            '6': {'key': 'apparent_temperature', 'length': '10', 'max': '49.9', 'min': '-39.9', 'step': '0.1'},
            '7': {'key': 'humidity', 'length': '7', 'max': '100', 'min': '0', 'step': '1'},
            '8': {'key': 'station_name', 'length': '4'},
            '9': {'key': 'date', 'length': '4'},
            '10': {'key': 'wind_direction_code', 'length': '4'},
            '11': {'key': 'sight_distance', 'length': '4'},
            '12': {'key': 'rain_mm_per_hour', 'length': '4'},
            '13': {'key': 'temperature_10_cm', 'length': '4'},
            '14': {'key': 'barometric_trend', 'length': '4'},
            '15': {'key': 'data_from_fallback', 'length': '4'},
            '16': {'key': 'latitude', 'length': '4'},
            '17': {'key': 'longitude', 'length': '4'},
            '18': {'key': 'DUMMY_BYTE', 'length': '4'},
        },
        'channel': 0,
        'extended-error-mode': False,
        'frequency': 250000,
        'interval': 300,
        'library': 'wiringPi',
        'source': 'buienradar',
        'stations': [6275]
    }
    bp = BuienradarParser(**config)
    context.result = bp.parse(data=context.weather_data_json)
