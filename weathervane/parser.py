import datetime
import logging
from json import JSONDecoder
from configparser import ConfigParser

from weathervane.weather import Weather


class BuienradarJSONDecoder(JSONDecoder):
    INVALID_DATA = ['-', '', None]

    def __init__(self):
        JSONDecoder.__init__(self, object_hook=self.dict_to_object)

    def dict_to_object(self, s):
        if type(s) == dict:
            for key, value in s.items():
                try:
                    if type(value) != dict and type(value) != list:
                        s[key] = datetime.datetime.strptime(value, '%m-%d-%Y %H:%M:%S')
                except ValueError:
                    try:
                        if type(value) != dict and type(value) != list:
                            s[key] = datetime.datetime.strptime(value, '%m/%d/%Y %H:%M:%S')
                    except (ValueError, TypeError):
                        pass

                if value in self.INVALID_DATA:
                    if key in ['regenMMPU', 'zonintensiteitWM2']:
                        s[key] = 0
                    s[key] = None
                    continue

                try:
                    s[key] = int(value)
                    continue
                except (ValueError, TypeError):
                    pass

                try:
                    s[key] = float(value)
                    continue
                except (ValueError, TypeError):
                    pass
        return s


class WeathervaneConfigParser(ConfigParser):
    DEFAULT_STATIONS = [6260, 6370]

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
        try:
            station_numbers = self['Stations']
        except KeyError:
            logging.error('Stations sections in config is formatted incorrectly. Using default stations')
            return self.DEFAULT_STATIONS

        stations = []
        station_id = None
        for i in range(len(station_numbers)):
            try:
                station_id = int(self['Stations'][str(i)])
            except KeyError:
                pass
            if station_id:
                stations.append(station_id)
        return stations

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
        logging.info('Configuration:', configuration)
        return configuration


class BuienradarParser(object):
    DERIVED_FIELDS = ['error', 'DUMMY_BYTE', 'barometric_trend', 'data_from_fallback', 'random', 'apparent_temperature']
    FIELD_MAPPING = {
        'air_pressure': 'luchtdruk',
        'date': 'datum',
        'humidity': 'luchtvochtigheid',
        'latitude': 'lat',
        'longitude': 'lon',
        'rain': 'regenMMPU',
        'rain_mm_per_hour': 'regenMMPU',
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
        'service_byte': 'service_byte'
    }
    TREND_MAPPING = {
        -1: 2,
        0: 4,
        1: 1
    }

    def __init__(self, *args, **kwargs):
        self.fallback_used = None
        self.stations = kwargs.get('stations', None)
        self.bits = kwargs.get('bits', None)

    def parse(self, data):
        assert type(data) == str
        decoder = BuienradarJSONDecoder()
        raw_weather_data = decoder.decode(data)
        raw_stations_weather_data = self._to_dict(
            raw_weather_data['buienradarnl']['weergegevens']['actueel_weer']['weerstations']['weerstation']
        )
        raw_primary_station_data = self.merge(raw_stations_weather_data, self.stations)
        station_weather_data = self.enrich(raw_primary_station_data)

        fields = self.extract_field_names(self.bits)
        weather_data = self.map(station_weather_data, fields)
        return weather_data

    @staticmethod
    def extract_field_names(bits_dict):
        result = []
        for v in bits_dict.values():
            result.append(v['key'])

        return result

    @staticmethod
    def enrich(weather_data):
        weather_data['apparent_temperature'] = BuienradarParser.calculate_temperature(weather_data)
        # TODO: store data in sqlite db for trend mapping
        weather_data['barometric_trend'] = 4
        return weather_data

    @staticmethod
    def merge(weather_data, stations):
        primary_station = stations[0]
        weather_data[primary_station]['data_from_fallback'] = False
        weather_data[primary_station]['error'] = False
        assert primary_station
        secondary_stations = stations[1:]
        if not secondary_stations:
            return weather_data[primary_station]
        for key, value in weather_data[primary_station].items():
            if not value and key not in BuienradarParser.DERIVED_FIELDS:
                for secondary_station in secondary_stations:
                    if weather_data.get(secondary_station, {}).get(key, None):
                        weather_data[primary_station][key] = weather_data[secondary_station][key]
                        weather_data[primary_station]['data_from_fallback'] = True
                        break
                else:
                    logging.warning('No backup value found')
                    weather_data[primary_station]['error'] = True
        return weather_data[primary_station]

    @staticmethod
    def calculate_temperature(weather_data):
        windspeed = weather_data['windsnelheidMS']
        temperature = weather_data['temperatuurGC']
        humidity = weather_data['luchtvochtigheid']
        return Weather.apparent_temperature(windspeed=windspeed, temperature=temperature, humidity=humidity)

    @staticmethod
    def _to_dict(stations_weather_data):
        return {station_data['@id']: station_data for station_data in stations_weather_data}

    @staticmethod
    def map(weather_data, fields):
        r = {}
        for field in fields:
            r[field] = weather_data.get(BuienradarParser.FIELD_MAPPING[field], None)
            if field == 'station_name':
                r[field] = r['station_name']['#text']
        return r
