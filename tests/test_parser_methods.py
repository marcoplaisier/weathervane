from weathervane.parser import BuienradarParser


def test_merge_with_fallback():
    """Tests whether the data can be retrieved from another station if the primary is lacking a specific field"""
    weather_data = {1: {"luchtdruk": None}, 2: {"luchtdruk": 1001}}

    bp = BuienradarParser(stations=None, bits=None)
    merged_data = bp.merge(weather_data, [1, 2], required_fields=[{"key": "luchtdruk"}])
    assert merged_data == {
        "data_from_fallback": True,
        "error": False,
        "luchtdruk": 1001,
    }


def test_merge_without_fallback():
    """Tests whether data from the primary station is always used when it is present"""
    weather_data = {1: {"luchtdruk": 1000}, 2: {"luchtdruk": 1001}}

    bp = BuienradarParser(stations=None, bits=None)
    merged_data = bp.merge(weather_data, [1, 2], required_fields=[{"key": "luchtdruk"}])
    assert merged_data == {
        "data_from_fallback": False,
        "error": False,
        "luchtdruk": 1000,
    }


def test_single_station():
    """Tests whether, if no fallback stations are selected, the data from the primary station is returned even if it
    is missing"""
    weather_data = {1: {"luchtdruk": None}, 2: {"luchtdruk": 1001}}

    bp = BuienradarParser(stations=None, bits=None)
    merged_data = bp.merge(weather_data, stations=[1], required_fields={"key": "luchtdruk"})
    assert merged_data == {
        "data_from_fallback": False,
        "error": False,
        "luchtdruk": None,
    }
