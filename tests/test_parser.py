import os

import pytest

from weathervane.parser import BuienradarParser


@pytest.fixture
def complete_weather_data():
    file_path = os.path.join(os.getcwd(), 'tests', 'buienradar.json')
    with open(file_path, 'r', encoding='UTF-8') as f:
        data = f.read()
        config = {
            'stations': [6275],
            'bits': [
                {'key': 'winddirection'},
                {'key': 'windspeed'},
                {'key': 'windgusts'},
                {'key': 'windspeedBft'},
                {'key': 'airpressure'},
                {'key': 'temperature'},
                {'key': 'feeltemperature'},
                {'key': 'humidity'},
                {'key': 'stationname'},
                {'key': 'lat'},
                {'key': 'lon'},
                {'key': 'winddirection'},
                {'key': 'visibility'},
                {'key': 'precipitation'},
                {'key': 'groundtemperature'},
                {'key': 'barometric_trend'},
                {'key': 'data_from_fallback'},
                {'key': 'rainFallLastHour'},
                {'key': 'rainFallLast24Hour'}
            ]
        }
        bp = BuienradarParser(**config)
        return {'data': bp.parse(data=data), 'config': config}


@pytest.fixture
def weather_data_with_fallback():
    file_path = os.path.join(os.getcwd(), 'tests', 'buienradar.json')
    with open(file_path, 'r', encoding='UTF-8') as f:
        data = f.read()
        config = {
            'stations': [6308, 6275],
            'bits': [
                {'key': 'winddirection'},
                {'key': 'windspeed'},
                {'key': 'windgusts'},
                {'key': 'windspeedBft'},
                {'key': 'airpressure'},
                {'key': 'temperature'},
                {'key': 'feeltemperature'},
                {'key': 'humidity'},
                {'key': 'stationname'},
                {'key': 'lat'},
                {'key': 'lon'},
                {'key': 'winddirection'},
                {'key': 'visibility'},
                {'key': 'precipitation'},
                {'key': 'groundtemperature'},
                {'key': 'barometric_trend'},
                {'key': 'data_from_fallback'},
                {'key': 'rainFallLastHour'},
                {'key': 'rainFallLast24Hour'}
            ]
        }
        bp = BuienradarParser(**config)
        return {'data': bp.parse(data=data), 'config': config}


def test_if_all_fields_are_available(complete_weather_data):
    for item in complete_weather_data['config']['bits']:
        field_name = item['key']
        try:
            complete_weather_data['data'][field_name]
        except KeyError:
            pytest.fail(f"Field {field_name} was not present in weather data")


def test_if_all_fields_are_available_with_fallback(weather_data_with_fallback):
    for item in weather_data_with_fallback['config']['bits']:
        field_name = item['key']
        try:
            weather_data_with_fallback['data'][field_name]
        except KeyError:
            pytest.fail(f"Field {field_name} was not present in weather data")


def test_windspeed_for_station_6275(complete_weather_data):
    windspeed = complete_weather_data['data']['windspeed']
    assert windspeed == 3.3


def test_feeltemperature_for_station_6275(complete_weather_data):
    feeltemperature = complete_weather_data['data']['feeltemperature']
    assert feeltemperature == 20.2


def test_missing_visibility_for_station_6308(weather_data_with_fallback, complete_weather_data):
    visibility_fallback = weather_data_with_fallback['data']['visibility']
    visibility_complete = complete_weather_data['data']['visibility']
    assert visibility_fallback == visibility_complete
