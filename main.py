#!/usr/bin/env python
import argparse
import asyncio
import logging
import time

import httpx

from weathervane.datasources import BuienRadarDataSource
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import Display, WeatherVaneInterface

NON_INTERPOLATABLE_VARIABLES = ["error", "winddirection", "winddirection", "rain", "barometric_trend"]
SLEEP_INTERVAL = 0.1

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")

# Configure logging to both file and stdout
# File logging for detailed application logs (systemd handles rotation)
file_handler = logging.FileHandler("/var/log/weathervane.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Stream logging for systemd journal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class TestDisplay:
    async def tick(self):
        pass


class WeatherVane(object):
    def __init__(self, *args, **configuration):
        self.old_weatherdata = None
        self.stations = configuration.get('stations')
        self.bits = configuration.get('bits')
        self.args = args
        self.configuration = configuration
        self.interface = WeatherVaneInterface(*args, **configuration)

        if not configuration.get("test", False):
            self.display = Display(**configuration["display"])
        else:
            self.display = TestDisplay()
        logger.info("Using " + str(self.interface))
        self.wd = None
        self.data_collection_interval = configuration["data_collection_interval"]
        self.data_display_interval = configuration["data_display_interval"]
        self.start_collection_time = time.monotonic()
        self.end_collection_time = time.monotonic()
        self.queue = asyncio.Queue(maxsize=1)
        self.data_source = BuienRadarDataSource(self.queue, self.stations, self.bits)

    async def start_data_collection(self):
        await asyncio.create_task(self.data_source.fetch_weather_data())

    async def retrieve_data(self):
        wd = self.queue.get_nowait()
        self.old_weatherdata, self.wd = self.wd, wd
        logger.info("weather data", extra=wd)
        return wd

    @staticmethod
    def interpolate(old_weatherdata, new_weatherdata, percentage):
        percentage = min(percentage, 1)
        if new_weatherdata["error"]:
            return new_weatherdata
        if not old_weatherdata:
            return new_weatherdata

        interpolated_wd = {}

        for key, old_value in old_weatherdata.items():
            new_value = new_weatherdata.get(key, None)
            if not new_value:
                interpolated_wd[key] = old_value
            elif key in NON_INTERPOLATABLE_VARIABLES:
                interpolated_wd[key] = new_value
            else:
                try:
                    interpolated_wd[key] = float(old_value) + (percentage * (float(new_value) - float(old_value)))
                except ValueError:
                    interpolated_wd[key] = new_value
                except TypeError:
                    interpolated_wd[key] = new_value

        return interpolated_wd

    async def loop(self):
        prev_data_collection_start_time = time.monotonic()
        prev_display_data_send_time = time.monotonic()
        await self.start_data_collection()
        wd = None

        while True:
            await self.display.tick()

            if time.monotonic() - prev_data_collection_start_time > self.data_collection_interval:
                prev_data_collection_start_time = time.monotonic()
                logger.debug("Starting weather data collection from BuienRadar")
                asyncio.create_task(self.data_source.fetch_weather_data())

            while not self.queue.empty():
                wd = await self.retrieve_data()

            display_time_elapsed = time.monotonic() - prev_display_data_send_time
            if wd and display_time_elapsed > self.data_display_interval:
                prev_display_data_send_time = time.monotonic()
                percentage = display_time_elapsed / self.data_collection_interval
                interpolated_wd = self.interpolate(self.old_weatherdata, wd, percentage)
                logger.debug(f"Sending interpolated weather data to interface: {interpolated_wd}")
                self.interface.send(interpolated_wd)
                logger.debug("Weather data sent successfully")

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

    wv_config = get_configuration(args)
    logger.info("Weathervane started with properties", extra=wv_config)
    wv = WeatherVane(**wv_config)
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
