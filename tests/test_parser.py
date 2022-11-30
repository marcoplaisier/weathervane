import os

import pytest

from weathervane.parser import BuienradarParser

bits = [
    {"key": "winddirection"},
    {"key": "windspeed"},
    {"key": "windgusts"},
    {"key": "windspeedBft"},
    {"key": "airpressure"},
    {"key": "temperature"},
    {"key": "feeltemperature"},
    {"key": "humidity"},
    {"key": "stationname"},
    {"key": "lat"},
    {"key": "lon"},
    {"key": "winddirection"},
    {"key": "visibility"},
    {"key": "precipitation"},
    {"key": "groundtemperature"},
    {"key": "barometric_trend"},
    {"key": "data_from_fallback"},
    {"key": "rainFallLastHour"},
    {"key": "rainFallLast24Hour"},
]


def load_test_data(stations):
    file_path = os.path.join(os.getcwd(), "tests", "buienradar.json")
    with open(file_path, "r", encoding="UTF-8") as f:
        data = f.read()
        config = {
            "stations": stations,
            "bits": bits,
        }
        bp = BuienradarParser(**config)
        return {"data": bp.parse(data=data), "config": config}


@pytest.fixture
def complete_weather_data():
    return load_test_data(stations=[6275])


@pytest.fixture
def weather_data_with_fallback():
    return load_test_data(stations=[6308, 6275])


def test_some_fields_for_station_6275(complete_weather_data):
    expected = {"windspeed": 3.3, "feeltemperature": 20.2}
    for k in expected.keys():
        windspeed = complete_weather_data["data"][k]
        assert windspeed == expected[k]


def test_missing_visibility_for_station_6308(
    weather_data_with_fallback, complete_weather_data
):
    visibility_fallback = weather_data_with_fallback["data"]["visibility"]
    visibility_complete = complete_weather_data["data"]["visibility"]
    assert visibility_fallback == visibility_complete
