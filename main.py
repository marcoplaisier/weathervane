#!/usr/bin/env python
import argparse
import datetime
import logging.handlers
import time
from multiprocessing import Pipe, Process

from pythonjsonlogger import jsonlogger

from weathervane.datasources import fetch_weather_data
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import Display, WeatherVaneInterface


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


logger = logging.getLogger("weathervane")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(
    filename="weathervane.log", when="midnight", interval=1, backupCount=1
)
stream_handler = logging.StreamHandler()
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
stream_handler.setFormatter(formatter)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(stream_handler)


class WeatherVane(object):
    def __init__(self, *args, **configuration):
        self.old_weatherdata = None
        self.args = args
        self.configuration = configuration
        self.interface = WeatherVaneInterface(*args, **configuration)
        self.display = Display(self.interface, **configuration["display"])
        logger.info("Using " + str(self.interface))
        self.wd = None
        self.counter = 0
        self.interval = configuration["interval"]
        self.sleep_time = configuration["sleep-time"]
        self.start_collection_time = datetime.datetime.now()
        self.end_collection_time = datetime.datetime.now()
        self.reached = False

    def start_data_collection(self, pipe_end):
        """Side effect: reset counter to 0

        @param pipe_end_1:
        @return:
        """
        self.counter = 0
        arguments = [pipe_end]
        arguments.extend(self.args)
        p = Process(
            target=fetch_weather_data, args=arguments, kwargs=self.configuration
        )
        p.start()
        logger.debug("Retrieving data")

    def send_data(self):
        if self.old_weatherdata:
            wd = self.interpolate(self.old_weatherdata, self.wd, self.interval)
            self.interface.send(wd)
        else:
            self.interface.send(self.wd)

    def retrieve_data(self, pipe_end_2):
        logger.info("Data available")
        self.end_collection_time = datetime.datetime.now()
        self.reached = False
        logger.info(
            "Data retrieval including parsing took {}".format(
                self.end_collection_time - self.start_collection_time
            )
        )
        self.old_weatherdata, self.wd = self.wd, pipe_end_2.recv()
        logger.info("weather data", extra=self.wd)

    def start_data_collection_and_timer(self, pipe_end_1):
        self.start_collection_time = datetime.datetime.now()
        self.start_data_collection(pipe_end_1)

    def log_heartbeat(self):
        logger.debug("Heartbeat-{}".format(self.counter))

    def interpolate(self, old_weatherdata, new_weatherdata, interval):
        if self.counter >= interval - 1:
            self.reached = True
        if new_weatherdata["error"]:
            return new_weatherdata

        interpolated_wd = {}

        for key, old_value in list(old_weatherdata.items()):
            new_value = new_weatherdata.get(key, None)
            if not new_value:
                continue

            if (
                    key
                    not in [
                "error",
                "winddirection",
                "winddirection",
                "rain",
                "barometric_trend",
            ]
                    and not self.reached
            ):
                try:
                    interpolated_value = float(old_value) + (
                            self.counter * (float(new_value) - float(old_value)) / interval
                    )
                    interpolated_wd[key] = interpolated_value
                except ValueError:
                    interpolated_wd[key] = new_value
                except TypeError:
                    interpolated_wd[key] = new_value
            else:
                interpolated_wd[key] = new_value

        return interpolated_wd

    def main(self):
        pipe_end_1, pipe_end_2 = Pipe()

        while True:
            self.display.tick()

            if (self.counter % 3) == 0:
                self.log_heartbeat()
            if (self.counter % self.interval) == 0:
                self.start_data_collection_and_timer(pipe_end_1)
            if pipe_end_2.poll(0):
                self.retrieve_data(pipe_end_2)
            if self.wd:
                self.send_data()
            self.counter += 1
            time.sleep(self.sleep_time)


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
