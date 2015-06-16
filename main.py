#!/usr/bin/env python
import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
import os
from time import sleep
import datetime

from weathervane.gpio import TestInterface
from weathervane.datasources import fetch_weather_data
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import WeatherVaneInterface


class WeatherVane(object):
    def __init__(self, *args, **configuration):
        self.args = args
        self.configuration = configuration
        self.interface = WeatherVaneInterface(*args, **configuration)
        logging.info("Using " + str(self.interface))
        self.wd = None
        self.counter = 0
        self.interval = configuration['interval']
        self.sleep_time = configuration['sleep-time']
        self.start_collection_time = 0
        self.end_collection_time = 0

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

    def check_selected_station(self, selected_station):
        """Check if another station is selected and change it when it has

        Determine whether the selected station has changed on the interface. If it has changed, then immediately start
        using data from this new station and return the id of the newly selected station.
        In the config-file you can specify a list of stations where data may be collected from. You can choose the
        specific station by also specifying on or more pins on the raspberry that together form a bitwise number.
        E.g you want to select one of four stations. You will need to specify 2 pins on the raspberry (2**2) that select
        on of these four stations. If pin 0 is high and pin 1 is low, you will select station 2. If both pins are high,
        you will select station 3, etc.

        Side effect: reset counter to 0 if another station is selected

        @param selected_station: the currently used station
        @return: either the id of the new station or the id of the station already in use
        """
        station_id = self.interface.selected_station
        if station_id != selected_station:  # reset if a new station is selected
            self.counter = 0
            logging.info("New station selected: {}".format(station_id))
        return station_id

    def start_data_collection(self, pipe_end_1, station_id):
        """Side effect: reset counter to 0

        @param pipe_end_1:
        @param station_id:
        @return:
        """
        self.counter = 0
        arguments = [pipe_end_1, station_id]
        arguments.extend(self.args)
        p = Process(target=fetch_weather_data, args=arguments, kwargs=self.configuration)
        p.start()
        logging.debug('Retrieving data')

    def main(self):
        """


        """
        pipe_end_1, pipe_end_2 = Pipe()
        selected_station = self.interface.selected_station

        while True:
            if (self.counter % 3) == 0:  # check the station selection every three seconds
                station_id = self.check_selected_station(selected_station)
                logging.debug('Heartbeat-{}'.format(self.counter))
            if (self.counter % self.interval) == 0:
                self.start_collection_time = datetime.datetime.now()
                self.start_data_collection(pipe_end_1, station_id)
            if pipe_end_2.poll(0):
                logging.debug('Data available:')
                self.end_collection_time = datetime.datetime.now()
                logging.info('Data parsing took {}'.format(self.end_collection_time-self.start_collection_time))
                self.wd = pipe_end_2.recv()
            if self.wd:
                self.interface.send(self.wd)
            self.counter += 1
            sleep(self.sleep_time)

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
        # weathervane_logger.addHandler(logging.StreamHandler())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-c', '--config', action='store', default='config.ini',
                        help="get the configuration from a specific configuration file")
    supplied_args = parser.parse_args()

    config_parser = WeathervaneConfigParser()
    config_file_location = os.path.join(os.getcwd(), supplied_args.config)
    config_parser.read(config_file_location)
    config = config_parser.parse_config()

    if config.get('test', False):
        print 'Testing mode engaged'

    wv = WeatherVane(**config)
    wv.set_logger()
    logging.info(supplied_args)
    wv.main()