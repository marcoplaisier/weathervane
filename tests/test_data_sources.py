from multiprocessing import Pipe

from weathervane.datasources import fetch_weather_data


def test_fetch():
    p1, p2 = Pipe()
    bits = {
        '0': {'key': 'winddirection'},
        '1': {'key': 'windspeed'},
        '2': {'key': 'windgusts'},
        '3': {'key': 'windspeedBft'},
        '4': {'key': 'airpressure'}}
    fetch_weather_data(p1, stations=[6209], bits=bits)
    p2.poll(timeout=5)
    data = p2.recv()
    assert 'winddirection' in data
    assert 'windspeed' in data
    assert 'windgusts' in data
    assert 'windspeedBft' in data
    assert 'airpressure' in data
