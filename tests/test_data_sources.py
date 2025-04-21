import asyncio
import inspect
from unittest.mock import MagicMock, patch

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


def test_weather_data_collection():
    """Test the direct awaiting of fetch_weather_data() instead of creating and immediately awaiting a task."""
    from main import WeatherVane
    
    # We can verify the method has been fixed by checking the source code:
    source = inspect.getsource(WeatherVane.start_data_collection)
    
    # Check that the method now directly awaits fetch_weather_data() and doesn't use create_task
    assert "await self.data_source.fetch_weather_data()" in source
    assert "asyncio.create_task" not in source or "# " in source.split("asyncio.create_task")[0]
