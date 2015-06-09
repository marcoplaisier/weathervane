from ConfigParser import SafeConfigParser
import datetime
import logging
from BeautifulSoup import BeautifulSoup


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
            'interrupt': self.getint('SPI', 'interrupt'),
            'interval': self.getint('General', 'interval'),
            'source': self.get('General', 'source'),
            'sleep-time': float(self.get('General', 'sleep-time')),
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
    INVALID_DATA = ['0', 0, '-', '', None]
    FIELD_MAPPING = {
        'wind_direction': 'windrichting',
        'wind_direction_degrees': 'windrichtingGR',
        'wind_speed': 'windsnelheidMS',
        'wind_speed_max': 'windstotenMS',
        'wind_speed_bft': 'windsnelheidBF',
        'air_pressure': 'luchtdruk',
        'temperature': 'temperatuurGC',
        'wind_chill': 'wind_chill',
        'humidity': 'luchtvochtigheid',
        'station_name': 'stationnaam',
        'latitude': 'lat',
        'longitude': 'lon',
        'date': 'datum',
        'wind_direction_code': 'windrichting',
        'sight_distance': 'zichtmeters',
        'rain_mm_per_hour': 'regenMMPU',
        'temperature_10_cm': 'temperatuur10cm'
    }

    @staticmethod
    def field_names(field_definitions):
        english_field_names = [field_definitions[number]['key'] for number in field_definitions.keys() if
                               field_definitions[number]['key'] in BuienradarParser.FIELD_MAPPING]
        return english_field_names

    @staticmethod
    def parse(data, station, *args, **kwargs):
        soup = BeautifulSoup(data)
        fallback = kwargs['fallback-station']
        fields = BuienradarParser.field_names(kwargs['bits'])
        get_data = BuienradarParser.get_data_from_station(soup, str(station), fallback)
        data = {field_name: get_data(BuienradarParser.FIELD_MAPPING[field_name]) for field_name in fields}
        return data

    @staticmethod
    def get_data_from_station(soup, station, fallback=None):
        def get_data(field_name):
            if field_name == 'wind_chill':
                return BuienradarParser.get_wind_chill(soup, station, fallback)

            station_data = soup.find("weerstation", id=station).find(field_name.lower())

            if station_data in BuienradarParser.INVALID_DATA or station_data.string in BuienradarParser.INVALID_DATA:
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
        wind_chill = 13.12 + 0.6215 * temperature - 13.96 * wind_speed ** 0.16 + 0.4867 * temperature * wind_speed ** 0.16
        return round(wind_chill, 0)