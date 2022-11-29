import os

from behave import given, step, then, use_step_matcher, when

from weathervane.parser import BuienradarParser

use_step_matcher("re")


@then("usable weatherdata is returned")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assert context.result["winddirection"] == "WZW"
    assert context.result["windspeed"] == 3.3
    assert context.result["windgusts"] == 5.5
    assert context.result["windspeedBft"] == 2
    assert context.result["airpressure"] == 1014.8
    assert context.result["temperature"] == 20.2
    assert context.result["feeltemperature"] == 20.2
    assert context.result["humidity"] == 73.0
    assert context.result["timestamp"] == "2021-06-19T13:40:00"
    assert context.result["visibility"] == 18100.0
    assert context.result["precipitation"] == 45.2
    assert context.result["groundtemperature"] == 21.4
    assert context.result["barometric_trend"] == 4
    assert context.result["data_from_fallback"] == False
    assert context.result["lat"] == 52.07
    assert context.result["lon"] == 5.88
    assert context.result["stationname"] == "Meetstation Arnhem"


@given("data from buienradar in json format")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    file_path = os.path.join(os.getcwd(), "tests", "buienradar.json")

    with open(file_path, "r", encoding="utf-8") as f:
        data = f.read()
        context.weather_data_json = data


@when("the data is parsed")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    config = {
        "bits": {
            "0": {"key": "winddirection", "length": "4"},
            "1": {
                "key": "windspeed",
                "length": "6",
                "max": "63",
                "min": "0",
                "step": "1",
            },
            "2": {
                "key": "windgusts",
                "length": "6",
                "max": "63",
                "min": "0",
                "step": "1",
            },
            "3": {
                "key": "windspeedBft",
                "length": "4",
                "max": "12",
                "min": "1",
                "step": "1",
            },
            "4": {
                "key": "airpressure",
                "length": "8",
                "max": "1155",
                "min": "900",
                "step": "1",
            },
            "5": {
                "key": "temperature",
                "length": "10",
                "max": "49.9",
                "min": "-39.9",
                "step": "0.1",
            },
            "6": {
                "key": "feeltemperature",
                "length": "10",
                "max": "49.9",
                "min": "-39.9",
                "step": "0.1",
            },
            "7": {
                "key": "humidity",
                "length": "7",
                "max": "100",
                "min": "0",
                "step": "1",
            },
            "8": {"key": "stationname", "length": "4"},
            "9": {"key": "date", "length": "4"},
            "10": {"key": "visibility", "length": "4"},
            "11": {"key": "precipitation", "length": "4"},
            "12": {"key": "groundtemperature", "length": "4"},
            "13": {"key": "barometric_trend", "length": "4"},
            "14": {"key": "data_from_fallback", "length": "4"},
            "15": {"key": "lat", "length": "4"},
            "16": {"key": "lon", "length": "4"},
            "17": {"key": "DUMMY_BYTE", "length": "4"},
        },
        "channel": 0,
        "extended-error-mode": False,
        "frequency": 250000,
        "interval": 300,
        "library": "wiringPi",
        "source": "buienradar",
        "stations": [6275],
    }
    bp = BuienradarParser(**config)
    context.result = bp.parse(data=context.weather_data_json)
