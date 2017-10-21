#!/usr/bin/env python
import argparse
import logging
import logging.handlers
import pprint
from multiprocessing import Process, Pipe
import os
import datetime
import time

from raven import Client

from weathervane.gpio import TestInterface
from weathervane.datasources import fetch_weather_data
from weathervane.parser import WeathervaneConfigParser
from weathervane.weathervaneinterface import WeatherVaneInterface, Display


class WeatherVane(object):
    def __init__(self, *args, **configuration):
        self.old_weatherdata = None
        self.args = args
        self.configuration = configuration
        self.interface = WeatherVaneInterface(*args, **configuration)
        self.display = Display(self.interface, **configuration['display'])
        logging.info("Using " + str(self.interface))
        self.wd = None
        self.counter = 0
        self.interval = configuration['interval']
        self.sleep_time = configuration['sleep-time']
        self.start_collection_time = 0
        self.end_collection_time = 0
        self.reached = False

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
            time.sleep(1)

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

    def start_data_collection(self, pipe_end):
        """Side effect: reset counter to 0

        @param pipe_end_1:
        @return:
        """
        self.counter = 0
        arguments = [pipe_end]
        arguments.extend(self.args)
        p = Process(target=fetch_weather_data, args=arguments, kwargs=self.configuration)
        p.start()
        logging.debug('Retrieving data')

    def send_data(self, error_state):
        if self.old_weatherdata and not error_state:
            wd = self.interpolate(self.old_weatherdata, self.wd, self.interval)
            self.interface.send(wd)
        else:
            self.interface.send(self.wd)

    def handle_errors(self, error_state):
        try:
            error_state = self.wd['error']
        except KeyError:
            error_state = True
        if error_state:
            self.wd = self.old_weatherdata
            self.old_weatherdata = None
            self.counter = 0
            error_state = True
        return error_state

    def retrieve_data(self, pipe_end_2):
        logging.info('Data available:')
        self.end_collection_time = datetime.datetime.now()
        self.reached = False
        logging.info('Data retrieval including parsing took {}'.format(
            self.end_collection_time - self.start_collection_time))
        self.old_weatherdata, self.wd = self.wd, pipe_end_2.recv()
        logging.info(pprint.pformat(self.wd))

    def start_data_collection_and_timer(self, pipe_end_1):
        self.start_collection_time = datetime.datetime.now()
        self.start_data_collection(pipe_end_1)

    def log_heartbeat(self):
        logging.debug('Heartbeat-{}'.format(self.counter))

    def set_logger(self):
        weathervane_logger = logging.getLogger('')
        weathervane_logger.setLevel(logging.INFO)
        handler = logging.handlers.TimedRotatingFileHandler(filename="weathervane.log",
                                                            when="midnight",
                                                            interval=1,
                                                            backupCount=7)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
        handler.setFormatter(formatter)
        weathervane_logger.addHandler(handler)

    def interpolate(self, old_weatherdata, new_weatherdata, interval):
        if self.counter >= interval - 1:
            self.reached = True

        interpolated_wd = {}

        for key, old_value in list(old_weatherdata.items()):
            new_value = new_weatherdata[key]
            if key not in ['error', 'wind_direction', 'wind_direction', 'rain',
                           'barometric_trend'] and not self.reached:
                try:
                    interpolated_value = float(old_value) + (
                    self.counter * (float(new_value) - float(old_value)) / interval)
                    interpolated_wd[key] = interpolated_value
                except ValueError:
                    interpolated_wd[key] = new_value
                except TypeError:
                    interpolated_wd[key] = new_value
            else:
                interpolated_wd[key] = new_value

        return interpolated_wd

    def main(self):
        """


        """
        pipe_end_1, pipe_end_2 = Pipe()
        error_state = False

        while True:
            self.display.tick()

            if (self.counter % 3) == 0:
                self.log_heartbeat()
            if (self.counter % self.interval) == 0:
                self.start_data_collection_and_timer(pipe_end_1)
            if pipe_end_2.poll(0):
                self.retrieve_data(pipe_end_2)
                error_state = self.handle_errors(error_state)
            if self.wd:
                self.send_data(error_state)
            self.counter += 1
            time.sleep(self.sleep_time)
            

def get_configuration(args):
    config_file = args.config
    config_file_location = os.path.join(os.getcwd(), config_file)

    config_parser = WeathervaneConfigParser()
    config_parser.read(config_file_location)
    config = config_parser.parse_config()
    return config


if __name__ == "__main__":
    client = Client()

    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-c', '--config', action='store', default='config.ini',
                        help="get the configuration from a specific configuration file")
    args = parser.parse_args()
    logging.info(args)

    wv_config = get_configuration(args)
    wv = WeatherVane(**wv_config)
    wv.set_logger()

    wv.main()
