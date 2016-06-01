from configparser import ConfigParser
import datetime
import logging
import math

from collections import OrderedDict
from bs4 import BeautifulSoup

from weathervane.weather import Weather


class WeathervaneConfigParser(ConfigParser):
    def __init__(self):
        super(WeathervaneConfigParser, self).__init__()

    def parse_bit_packing_section(self):
        bit_numbers = self.options('Bit Packing')

        bits = {}
        for bit_number in bit_numbers:
            bit_config = self.get('Bit Packing', bit_number).split(',')
            if len(bit_config) == 2:
                bits[bit_number] = {
                    'key': bit_config[0],
                    'length': bit_config[1]
                }
            else:
                bits[bit_number] = {
                    'key': bit_config[0],
                    'length': bit_config[1],
                    'min': bit_config[2],
                    'max': bit_config[3],
                    'step': bit_config[4]
                }
        return bits

    def parse_station_numbers(self):
        station_numbers = self.options('Stations')

        station_config = {}
        for number in station_numbers:
            try:
                number = int(number)
                station_config[number] = self.get('Stations', str(number))
            except ValueError:
                logging.info("Option {} not recognized".format(number))
        return station_config

    def parse_config(self):
        """Takes a configuration parser and returns the configuration as a dictionary

        @return: configuration as dictionary
        """
        station_config = self.parse_station_numbers()
        bits = self.parse_bit_packing_section()

        configuration = {
            'extended-error-mode': self.getboolean('General', 'extended-error-mode'),
            'channel': self.getint('SPI', 'channel'),
            'frequency': self.getint('SPI', 'frequency'),
            'library': self.get('SPI', 'library'),
            'interval': self.getint('General', 'interval'),
            'source': self.get('General', 'source'),
            'sleep-time': float(self.get('General', 'sleep-time')),
            'test': self.getboolean('General', 'test'),
            'barometric_trend': self.getboolean('General', 'barometric_trend'),
            'stations': station_config,
            'bits': bits,
            'display': {
                'auto-turn-off': self.getboolean('Display', 'auto-turn-off'),
                'start-time': self.get('Display', 'start-time'),
                'end-time': self.get('Display', 'end-time'),
                'pin': self.getint('Display', 'pin'),
            },
        }
        logging.debug('Configuration:', configuration)
        return configuration


class BuienradarParser(object):
    INVALID_DATA = ['-', '', None]
    FIELD_MAPPING = {
        'air_pressure': 'luchtdruk',
        'date': 'datum',
        'humidity': 'luchtvochtigheid',
        'latitude': 'lat',
        'longitude': 'lon',
        'rain': 'regenMMPU',
        'random': 'random',
        'sight_distance': 'zichtmeters',
        'temperature': 'temperatuurGC',
        'temperature_10_cm': 'temperatuur10cm',
        'station_name': 'stationnaam',
        'apparent_temperature': 'apparent_temperature',
        'wind_direction': 'windrichting',
        'wind_direction_code': 'windrichting',
        'wind_direction_degrees': 'windrichtingGR',
        'wind_speed': 'windsnelheidMS',
        'wind_speed_max': 'windstotenMS',
        'wind_speed_bft': 'windsnelheidBF',
        'data_from_fallback': 'data_from_fallback',
        'barometric_trend': 'barometric_trend',
        'error': 'error',
        'DUMMY_BYTE': 'DUMMY_BYTE',
    }
    TREND_MAPPING = {
        -1: 2,
        0: 4,
        1: 1
    }

    def __init__(self, *args, **kwargs):
        self.historic_data = dict()
        self.raw_xml = None
        default_stations = [6260, 6370]
        self.station = kwargs.get('stations', default_stations)[0]
        self.fallback = kwargs.get('stations', default_stations)[1]

    def get_fallback_station(self, stations):
        i = list(stations.values()).index(self.station)
        return stations[(i + 1) % len(stations)]

    def parse(self, raw_xml, *args, **kwargs):
        self.raw_xml = raw_xml
        self.get_data = self.get_parser_func()
        field_names = self.extract_field_names(kwargs['bits'])
        data = {}
        for english_name, dutch_name in BuienradarParser.FIELD_MAPPING.items():
            if english_name in field_names:
                data[english_name] = self.get_data(dutch_name)

        return data

    def extract_field_names(self, bits_dict):
        result = []
        for v in bits_dict.values():
            result.append(v['key'])

        try:
            present = result.index('data_from_fallback')
            if present:
                result.append(result.pop(present))
        except ValueError:
            pass

        return result

    def get_data_from_station(self, soup, fallback=False):
        def get_data(field_name):
            if fallback:
                station = self.fallback
            else:
                station = self.station

            if field_name == 'apparent_temperature':
                return self.calculate_temperature(soup, fallback)
            if field_name == 'data_from_fallback':
                return 0
            if field_name == 'barometric_trend':
                return self.calculate_barometric_trend()

            station_data = soup.find(id=station)
            weather_data = station_data.find(field_name.lower())

            if data_is_invalid(weather_data) and field_name != 'random':
                if field_name == 'regenMMPU':
                    return 0.0
                if not fallback:
                    logging.debug('Returning {} from fallback {}'.format(field_name, fallback))
                    get_data_from_fallback = self.get_data_from_station(soup, True)
                    return get_data_from_fallback(field_name)
                else:
                    logging.info('Field {} without valid data. Returning 0'.format(field_name))
                    return 0
            if field_name == 'datum':
                return datetime.datetime.strptime(weather_data.string, '%m/%d/%Y %H:%M:%S')
            if weather_data is None:
                return weather_data
            else:
                try:
                    data = weather_data.string
                    if field_name == 'windsnelheidBF':
                        return int(data)
                    else:
                        weather_data = float(weather_data.string)
                        if field_name == 'luchtdruk':
                            self.historic_data[self.get_data('datum')] = weather_data
                        return weather_data
                except ValueError:
                    return str(weather_data.string)

        def data_is_invalid(weather_data):
            return (weather_data in BuienradarParser.INVALID_DATA or
                    weather_data.string in BuienradarParser.INVALID_DATA)

        return get_data

    def calculate_barometric_trend(self):
        barometric_pressure = self.get_data('luchtdruk')
        current_time = self.get_data('datum')
        three_hours_ago = current_time - datetime.timedelta(hours=3)
        barometric_pressure_three_hours_ago = self.historic_data.get(three_hours_ago, None)
        if barometric_pressure_three_hours_ago is not None:
            difference = barometric_pressure - barometric_pressure_three_hours_ago
            if difference < 0:
                barometric_trend = -1
            elif difference > 0:
                barometric_trend = 1
            else:
                barometric_trend = 0
        else:
            barometric_trend = 0
        return self.TREND_MAPPING[barometric_trend]

    def calculate_temperature(self, soup, fallback=None):
        get_data = self.get_data_from_station(soup, fallback)
        windspeed = get_data('windsnelheidMS')
        temperature = get_data('temperatuurGC')
        humidity = get_data('luchtvochtigheid')
        return Weather.apparent_temperature(windspeed=windspeed, temperature=temperature, humidity=humidity)

    def get_barometric_trend_direction(self, data):
        self.historic_data.append(data['air_pressure'])
        self.historic_data = self.historic_data[-5:]
        barometric_trend = Statistics.barometric_trend(self.historic_data)
        return barometric_trend

    def get_parser_func(self):
        soup = BeautifulSoup(self.raw_xml, "html.parser")
        return self.get_data_from_station(soup, False)


class Statistics(object):
    @staticmethod
    def average(s):
        """Calculates the mean of the given sequence of numbers

        @param s: a sequence of numbers
        @return: the mean
        """
        if s:
            return sum(s) / float(len(s))
        else:
            return None

    @staticmethod
    def std_dev(s):
        """

        @param s:
        @return:
        """
        if len(s) in [0, 1]:
            return 0
        avg = Statistics.average(s)
        sum_of_squares = sum([(x - avg) ** 2 for x in s])
        return math.sqrt(sum_of_squares) / (len(s) - 1)

    @staticmethod
    def barometric_trend(s):
        if len(s) in [0, 1]:
            return 0
        stdev = Statistics.std_dev(s)
        average = Statistics.average(s)
        if s[-1] < (average - stdev):
            return -1
        elif s[-1] > (average + stdev):
            return 1
        else:
            return 0
