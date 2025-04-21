import logging
from asyncio import Queue
from typing import Dict, Any, Optional, List

import httpx

from weathervane.parser import BuienradarParser

HTTP_OK = 200

DEFAULT_WEATHER_DATA: Dict[str, Any] = {
    "error": True,
    "airpressure": 900,
    "humidity": 0,
    "rain": True,
    "random": 0,
    "temperature": -39.9,
    "groundtemperature": -39.9,
    "feeltemperature": 0,
    "winddirection": "N",
    "winddirectiondegrees": 0,
    "windspeed": 0,
    "windgusts": 0,
    "windspeedBft": 0,
}

logger = logging.getLogger()


class BuienRadarDataSource:

    def __init__(self, queue: Queue, stations: List[int], bits: List[Dict[str, Any]]) -> None:
        self.queue: Queue = queue
        self.bp: BuienradarParser = BuienradarParser(stations=stations, bits=bits)

    @staticmethod
    async def __get_weather() -> str:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://data.buienradar.nl/2.0/feed/json", timeout=5)

        if r.status_code == HTTP_OK:
            logger.info(f"Weather data retrieved in {r.elapsed} ms")
            return r.text
        else:
            logger.warning(f"Got response in {r.elapsed} ms, but unexpected status code {r.status_code}")
            raise ConnectionError(f"Buienradar: {r.status_code}")

    async def fetch_weather_data(self) -> None:
        data = await self.__get_weather()

        if data:
            try:
                wd = self.bp.parse(data)
            except ConnectionError as e:
                logger.error("Data parsing failed. Cannot send good data. Setting error.")
                wd = DEFAULT_WEATHER_DATA
        else:
            logger.error("Retrieving data failed several times. Setting error.")
            wd = DEFAULT_WEATHER_DATA

        await self.queue.put(wd)
