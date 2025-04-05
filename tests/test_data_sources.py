import asyncio

from weathervane.datasources import BuienRadarDataSource


async def test_fetch():
    queue = asyncio.Queue(maxsize=1)
    bits = [
        {"key": "winddirection"},
        {"key": "windspeed"},
        {"key": "windgusts"},
        {"key": "windspeedBft"},
        {"key": "airpressure"},
    ]
    bp = BuienRadarDataSource(queue=queue, stations=[6260], bits=bits)
    await bp.fetch_weather_data()
    data = await queue.get()
    assert "winddirection" in data
    assert "windspeed" in data
    assert "windgusts" in data
    assert "windspeedBft" in data
    assert "airpressure" in data
