from multiprocessing import Pipe

from weathervane.datasources import fetch_weather_data, DEFAULT_WEATHER_DATA


def test_fetch():
    p1, p2 = Pipe()
    bits = {
        '0': {'key': 'wind_direction'},
        '1': {'key': 'wind_speed'},
        '2': {'key': 'wind_speed_max'},
        '3': {'key': 'wind_speed_bft'},
        '4': {'key': 'air_pressure'}}
    fetch_weather_data(p1, stations=[6209], bits=bits)
    p2.poll(timeout=5)
    data = p2.recv()
    assert 'wind_direction' in data
    assert 'wind_speed' in data
    assert 'wind_speed_max' in data
    assert 'wind_speed_bft' in data
    assert 'air_pressure' in data
