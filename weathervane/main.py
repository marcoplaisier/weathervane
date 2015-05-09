#!/usr/bin/env python
import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
import os
from time import sleep

from gpio import TestInterface
from datasources import fetch_weather_data
from parser import WeathervaneConfigParser
from weathervaneinterface import WeatherVaneInterface


class WeatherVane(object):
    def test_mode(self):
        """
        Test mode is used to output a predicable sequence of bytes to
        the output pins.
        The program will send 3 bytes every second to the pins.
        - Byte 1: an increasing counter (modulo 255)
        - Byte 2: a decreasing counter (idem)
        - Byte 3: switches between 0x55 and 0xAA

        """
        logging.info("Starting test mode")
        interface = TestInterface(channel=0, frequency=25000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter % 255, (255 - counter) % 255, test]

            interface.send(data)
            sleep(1)

    def main(self, *args, **kwargs):
        interface = WeatherVaneInterface(*args, **kwargs)
        logging.debug("Using " + str(interface))
        wd = None
        pipe_end_1, pipe_end_2 = Pipe()
        counter = 0

        selected_station = interface.selected_station

        while True:
            if (counter % 3) == 0:  # check the station selection every three seconds
                station_id = interface.selected_station
                if station_id != selected_station:  # reset if a new station is selected
                    counter = 0
                    selected_station = station_id
                    logging.info("New station selected: {}".format(station_id))

            if (counter % kwargs['interval']) == 0:
                counter = 0
                arguments = [pipe_end_1, station_id]
                arguments.extend(args)
                p = Process(target=fetch_weather_data, args=arguments, kwargs=kwargs)
                p.start()
                logging.debug('Retrieving data')

            if pipe_end_2.poll(0):
                wd = pipe_end_2.recv()
                logging.debug('Received data:' + str(wd))

            if wd:
                interface.send(wd)

            logging.debug('Heartbeat-{}'.format(counter))
            counter += 1
            sleep(1)

    def set_logger(self):
        weathervane_logger = logging.getLogger('')
        weathervane_logger.setLevel(logging.DEBUG)
        handler = logging.handlers.TimedRotatingFileHandler(filename="weathervane.log",
                                                            when="midnight",
                                                            interval=1,
                                                            backupCount=7)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
        handler.setFormatter(formatter)
        weathervane_logger.addHandler(handler)
        weathervane_logger.addHandler(logging.StreamHandler())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-c', '--config', action='store', default='config.ini',
                        help="get the configuration from a specific configuration file")
    supplied_args = parser.parse_args()

    wv = WeatherVane()
    wv.set_logger()
    logging.info(supplied_args)

    config_parser = WeathervaneConfigParser()
    config_file_location = os.path.join(os.getcwd(), supplied_args.config)
    config_parser.read(config_file_location)
    config = config_parser.parse_config()

    if config.get('test', False):
        wv.test_mode()
    else:
        wv.main(**config)
