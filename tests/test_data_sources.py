from multiprocessing import Pipe

from weathervane.datasources import fetch_weather_data


def test_fetch():
    p1, p2 = Pipe()
    bits = [
        {"key": "winddirection"},
        {"key": "windspeed"},
        {"key": "windgusts"},
        {"key": "windspeedBft"},
        {"key": "airpressure"},
    ]
    fetch_weather_data(p1, stations=[6260], bits=bits)
    p2.poll(timeout=5)
    data = p2.recv()
    assert "winddirection" in data
    assert "windspeed" in data
    assert "windgusts" in data
    assert "windspeedBft" in data
    assert "airpressure" in data
