from ConfigParser import SafeConfigParser
import datetime
import logging
from BeautifulSoup import BeautifulSoup
import math
from random import randint


class WeathervaneConfigParser(SafeConfigParser):
    def __init__(self):
        SafeConfigParser.__init__(self)

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
                if number not in ['fallback', 'pins']:
                    logging.debug("Option not recognized")
        return station_config

    def parse_config(self):
        """Takes a configuration parser and returns the configuration as a dictionary

        @param cp:
        @return:
        """
        pins = map(int, self.get('Stations', 'pins').split(','))
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
            'trend': self.getboolean('General', 'trend'),
            'fallback-station': self.get('Stations', 'fallback'),
            'stations': {
                'pins': pins,
                'config': station_config
            },
            'bits': bits
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
        'wind_chill': 'wind_chill',
        'wind_direction': 'windrichting',
        'wind_direction_code': 'windrichting',
        'wind_direction_degrees': 'windrichtingGR',
        'wind_speed': 'windsnelheidMS',
        'wind_speed_max': 'windstotenMS',
        'wind_speed_bft': 'windsnelheidBF',
    }
    TREND_MAPPING = {
        -1: 2,
        0: 4,
        1: 1
    }

    def __init__(self):
        self.historic_data = []

    @staticmethod
    def field_names(field_definitions):
        english_field_names = [field_definitions[number]['key'] for number in field_definitions.keys() if
                               field_definitions[number]['key'] in BuienradarParser.FIELD_MAPPING]
        return english_field_names

    def parse(self, data, station, *args, **kwargs):
        soup = BeautifulSoup(data)
        fallback = kwargs['fallback-station']
        fields = BuienradarParser.field_names(kwargs['bits'])
        get_data = BuienradarParser.get_data_from_station(soup, str(station), fallback)
        data = {field_name: get_data(BuienradarParser.FIELD_MAPPING[field_name]) for field_name in fields}
        if 'trend' in kwargs.keys():
            trend = self.get_trend_direction(data)
            data['trend'] = self.TREND_MAPPING[trend]
        return data

    @staticmethod
    def get_data_from_station(soup, station, fallback=None):
        def get_data(field_name):
            if field_name == 'wind_chill':
                return BuienradarParser.get_wind_chill(soup, station, fallback)

            station_data = soup.find("weerstation", id=station).find(field_name.lower())

            if (station_data in BuienradarParser.INVALID_DATA or \
                    station_data.string in BuienradarParser.INVALID_DATA) and \
                    field_name != 'random':
                if field_name == 'regenMMPU':
                    return 0.0
                if fallback:
                    logging.debug('Returning {} from fallback {}'.format(field_name, fallback))
                    get_data_from_fallback = BuienradarParser.get_data_from_station(soup, fallback, None)
                    return get_data_from_fallback(field_name)
                else:
                    logging.debug('Field {} without valid data. Returning 0'.format(field_name))
                    return 0
            if field_name == 'datum':
                return datetime.datetime.strptime(station_data.string, '%m/%d/%Y %H:%M:%S')
            if station_data is None:
                return station_data
            else:
                try:
                    data = station_data.string
                    if field_name == 'windsnelheidBF':
                        return int(data)
                    else:
                        return float(station_data.string)
                except ValueError:
                    return station_data.string

        return get_data

    @staticmethod
    def station_codes(raw_xml):
        soup = BeautifulSoup(raw_xml)
        code_tags = soup("stationcode")
        codes = [int(tag.string) for tag in code_tags]
        return codes

    @staticmethod
    def get_wind_chill(soup, station, fallback=None):
        get_data = BuienradarParser.get_data_from_station(soup, station, fallback)
        wind_speed = get_data('windsnelheidMS')
        temperature = get_data('temperatuurGC')
        return BuienradarParser.calculate_wind_chill(wind_speed, temperature)

    @staticmethod
    def calculate_wind_chill(wind_speed, temperature):
        if wind_speed < 0:
            raise ValueError("Wind speed must be a positive number")
        wind_chill = 13.12 + 0.6215 * temperature - 13.96 * wind_speed ** 0.16 + 0.4867 * temperature * wind_speed ** 0.16
        return round(wind_chill, 0)

    def get_trend_direction(self, data):
        self.historic_data.append(data['air_pressure'])
        self.historic_data = self.historic_data[-5:]
        trend = Statistics.trend(self.historic_data)
        return trend


class Statistics(object):
    @staticmethod
    def average(s):
        """Calculates the mean of the given sequence of numbers

        @param s: a sequence of numbers
        @return: the mean
        """
        if s:
            return sum(s)/float(len(s))
        else:
            return None

    @staticmethod
    def std_dev(s):
        """

        @param s:
        @return:
        """
        if len(s) in [0,1]:
            return 0
        avg = Statistics.average(s)
        sum_of_squares = sum([(x-avg)**2 for x in s])
        return math.sqrt(sum_of_squares)/(len(s)-1)

    @staticmethod
    def trend(s):
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
