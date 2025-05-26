#!/usr/bin/env python
import argparse
import asyncio
import logging.handlers
import time
from typing import Optional

import httpx

from weathervane.datasources import BuienRadarDataSource
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import Display, WeatherVaneInterface
from weathervane.models import AppConfig, WeatherData

NON_INTERPOLATABLE_VARIABLES = ["error", "winddirection", "rain", "barometric_trend"] # Removed duplicate "winddirection"
SLEEP_INTERVAL = 0.1

logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
handler = logging.handlers.TimedRotatingFileHandler(
    filename="weathervane.log", when="midnight", interval=1, backupCount=1
)
handler.setFormatter(formatter)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
logger.addHandler(handler)


class TestDisplay:
    async def tick(self):
        pass


class WeatherVane(object):
    def __init__(self, config: AppConfig):
        self.old_weatherdata: Optional[WeatherData] = None
        self.wd: Optional[WeatherData] = None
        self.config = config
        self.interface = WeatherVaneInterface(config) # Pass AppConfig instance

        if not config.test:
            self.display = Display(**config.display.model_dump())
        else:
            self.display = TestDisplay()
        logger.info("Using " + str(self.interface))
        self.data_collection_interval = config.data_collection_interval
        self.data_display_interval = config.data_display_interval
        self.start_collection_time = time.monotonic() # This seems unused, but retained for now
        self.end_collection_time = time.monotonic()   # This seems unused, but retained for now
        self.queue = asyncio.Queue(maxsize=1)
        self.data_source = BuienRadarDataSource(self.queue, config.stations, config.bits)

    async def start_data_collection(self):
        await asyncio.create_task(self.data_source.fetch_weather_data())

    async def retrieve_data(self) -> WeatherData:
        wd: WeatherData = self.queue.get_nowait() # Data from queue is WeatherData
        self.old_weatherdata, self.wd = self.wd, wd
        logger.info("weather data", extra=wd.model_dump())
        return wd

    @staticmethod
    def interpolate(old_weatherdata: Optional[WeatherData], new_weatherdata: WeatherData, percentage: float) -> WeatherData:
        percentage = min(percentage, 1.0) # Ensure percentage is float and capped at 1.0
        
        if new_weatherdata.error:
            return new_weatherdata
        if not old_weatherdata:
            return new_weatherdata

        # Start with a copy of new_weatherdata values
        interpolated_values = new_weatherdata.model_dump()
        old_dict = old_weatherdata.model_dump()

        for key, new_value in interpolated_values.items():
            old_value = old_dict.get(key)

            if old_value is None: # Should not happen if old_weatherdata is WeatherData
                continue # Use new_value already in interpolated_values

            if key in NON_INTERPOLATABLE_VARIABLES:
                # Already set from new_weatherdata, so continue
                continue
            else:
                try:
                    # Ensure both values are numeric for interpolation
                    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                        interpolated_values[key] = float(old_value) + (percentage * (float(new_value) - float(old_value)))
                    # else, keep the new_value (non-numeric types, or type mismatch)
                except (ValueError, TypeError):
                    # In case of error, keep the new_value
                    pass # interpolated_values[key] is already new_value

        return WeatherData(**interpolated_values)

    async def loop(self):
        prev_data_collection_start_time = time.monotonic()
        prev_display_data_send_time = time.monotonic()
        await self.start_data_collection()
        wd = None

        while True:
            await self.display.tick()

            if time.monotonic() - prev_data_collection_start_time > self.data_collection_interval:
                prev_data_collection_start_time = time.monotonic()
                asyncio.create_task(self.data_source.fetch_weather_data())

            while not self.queue.empty():
                wd = await self.retrieve_data()

            display_time_elapsed = time.monotonic() - prev_display_data_send_time
            if wd and display_time_elapsed > self.data_display_interval:
                prev_display_data_send_time = time.monotonic()
                percentage = display_time_elapsed / self.data_collection_interval
                interpolated_wd = self.interpolate(self.old_weatherdata, wd, percentage)
                self.interface.send(interpolated_wd)

            await asyncio.sleep(SLEEP_INTERVAL)


def get_configuration(args):
    config_parser = WeathervaneConfigParser()
    config_file = args.config
    config_parser.read(config_file)
    config = config_parser.parse_config()
    return config


async def main():
    parser = argparse.ArgumentParser(
        description="Get weather data from a provider and send it through SPI"
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        default="config.ini",
        help="get the configuration from a specific configuration file",
    )
    args = parser.parse_args()

    wv_app_config: AppConfig = get_configuration(args) # wv_config is now AppConfig
    # For logging, Pydantic models have a nice string representation.
    # Using .model_dump() for the 'extra' parameter to provide a dictionary.
    logger.info("Weathervane started with properties", extra=wv_app_config.model_dump())
    wv = WeatherVane(wv_app_config) # Pass the AppConfig instance directly
    await wv.loop()


def wait_for_connection():
    connection = False
    sleep_time = 1
    while not connection:
        try:
            r = httpx.get("http://www.google.com")
            logger.info(f"Connection established with status code: {r.status_code}")
            connection = True
        except httpx.ConnectError:
            logger.error(f"No connection yet, waiting for {sleep_time} seconds")
            time.sleep(sleep_time)
            sleep_time = min(60, sleep_time * 2)


if __name__ == "__main__":
    try:
        wait_for_connection()
        asyncio.run(main())
    finally:
        logger.info("Shutting down")
