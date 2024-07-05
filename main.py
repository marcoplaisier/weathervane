#!/usr/bin/env python
import argparse
import logging.handlers
import multiprocessing
import time
from multiprocessing import Pipe, Process

from weathervane.datasources import fetch_weather_data
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import Display, WeatherVaneInterface

NON_INTERPOLATABLE_VARIABLES = ["error", "winddirection", "winddirection", "rain", "barometric_trend"]
SLEEP_INTERVAL = 0.1

logger = multiprocessing.get_logger()
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


class WeatherVane(object):
    def __init__(self, *args, **configuration):
        self.old_weatherdata = None
        self.args = args
        self.configuration = configuration
        self.interface = WeatherVaneInterface(*args, **configuration)
        self.display = Display(**configuration["display"])
        logger.info("Using " + str(self.interface))
        self.wd = None
        self.data_collection_interval = configuration["data_collection_interval"]
        self.data_display_interval = configuration["data_display_interval"]
        self.start_collection_time = time.monotonic()
        self.end_collection_time = time.monotonic()

    def start_data_collection(self, pipe_end):
        arguments = [pipe_end]
        arguments.extend(self.args)
        p = Process(
            target=fetch_weather_data, args=arguments, kwargs=self.configuration
        )
        p.start()

    def retrieve_data(self, pipe_end):
        wd = pipe_end.recv()
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

    def main(self):
        pipe_end_1, pipe_end_2 = Pipe()
        prev_data_collection_start_time = time.monotonic()
        prev_display_data_send_time = time.monotonic()
        self.start_data_collection(pipe_end_1)
        wd = None

        while True:
            self.display.tick()

            if time.monotonic() - prev_data_collection_start_time > self.data_collection_interval:
                prev_data_collection_start_time = time.monotonic()
                self.start_data_collection(pipe_end_1)
            if pipe_end_2.poll(0):
                wd = self.retrieve_data(pipe_end_2)

            display_time_elapsed = time.monotonic() - prev_display_data_send_time
            if wd and display_time_elapsed > self.data_display_interval:
                prev_display_data_send_time = time.monotonic()
                percentage = display_time_elapsed / self.data_collection_interval
                interpolated_wd = self.interpolate(self.old_weatherdata, wd, percentage)
                self.interface.send(interpolated_wd)

            time.sleep(SLEEP_INTERVAL)


def get_configuration(args):
    config_parser = WeathervaneConfigParser()
    config_file = args.config
    config_parser.read(config_file)
    config = config_parser.parse_config()
    return config


def run():
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
    wv.main()


if __name__ == "__main__":
    try:
        run()
    finally:
        logger.info("Shutting down")
