import asyncio
import os

from weathervane.datasources import BuienRadarDataSource
from weathervane.parser import WeathervaneConfigParser


async def test_recursion():
    q = asyncio.Queue(maxsize=1)
    cp = WeathervaneConfigParser()
    config_file = os.path.join(os.getcwd(), "tests", "config-test1.ini")
    cp.read(config_file)
    c = cp.parse_config()
    data_source = BuienRadarDataSource(q, stations=c.get('stations'), bits=c.get('bits'))
    await asyncio.create_task(data_source.fetch_weather_data())

    while q.empty():
        await asyncio.sleep(0.1)

    _ = await q.get()
