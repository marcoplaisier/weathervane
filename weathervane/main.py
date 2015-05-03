#!/usr/bin/env python
import ConfigParser

import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
import os
from time import sleep
from gpio import TestInterface

from weathervane.datasources import weather_data
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

    def get_source(self, source):
        if source == 'buienradar':
            from datasources import BuienradarSource

            return BuienradarSource()
        elif source == 'knmi':
            from datasources import KNMISource

            return KNMISource()
        elif source == 'rijkswaterstaat':
            from datasources import RijkswaterstaatSource

            return RijkswaterstaatSource()
        elif source == 'test':
            from datasources import TestSource

            return TestSource()
        else:
            raise NameError('Data provider not found')

    def main(self, *args, **kwargs):
        logging.info("Starting operation")
        interface = WeatherVaneInterface(*args, **kwargs)

        logging.debug("Using " + str(interface))
        wd = weather_data(wind_direction=None, wind_speed=None, wind_speed_max=None, air_pressure=None)

        data_source = self.get_source(kwargs['source'])

        pipe_end_1, pipe_end_2 = Pipe()
        counter = 0

        selected_station = interface.get_selected_station()

        while True:
            if (counter % 3) == 0:  # check the station selection every three seconds
                station_id = interface.get_selected_station()
                if station_id != selected_station:  # reset if a new station is selected
                    counter = 0
                    selected_station = station_id
                    logging.info("New station selected: {}".format(station_id))

            if (counter % kwargs['interval']) == 0:
                counter = 0
                p = Process(target=data_source.get_data, args=(pipe_end_1, station_id))
                p.start()

            if pipe_end_2.poll(0):
                wd = pipe_end_2.recv()
                logging.info("Received data:" + str(wd))

            interface.send(wd)

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


def parse_config(cp):
    """Takes a configuration parser and returns the configuration as a dictionary

    @param cp:
    @return:
    """
    pins = map(int, cp.get('Stations', 'pins').split(','))

    station_numbers = cp.options('Stations')
    station_config = {}
    for number in station_numbers:
        try:
            number = int(number)
            station_config[number] = cp.get('Stations', str(number))
        except ValueError:
            if not number in ['fallback', 'pins']:
                logging.debug("Option not recognized")

    bit_numbers = cp.options('Bit Packing')
    bits = {}
    for bit_number in bit_numbers:
        bit_config = cp.get('Bit Packing', bit_number).split(',')
        bits[bit_number] = {
            'key': bit_config[0],
            'length': bit_config[1]
        }

    configuration = {
        'channel': cp.getint('SPI', 'channel'),
        'frequency': cp.getint('SPI', 'frequency'),
        'library': cp.get('SPI', 'library'),
        'interval': cp.getint('General', 'interval'),
        'source': cp.get('General', 'source'),
        'stations': {
            'pins': pins,
            'config': station_config
        },
        'bits': bits
    }
    return configuration


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-c', '--config', action='store', default='config.ini',
                        help="get the configuration from a specific configuration file")
    args = parser.parse_args()

    wv = WeatherVane()
    wv.set_logger()
    logging.info(args)

    config_parser = ConfigParser.RawConfigParser()
    config_file_location = os.path.join(os.getcwd(), args.config)
    config_parser.read(config_file_location)
    config = parse_config(config_parser)

    if config.get('test', False):
        wv.test_mode()
    else:
        wv.main(**config)
