import json
import logging
from datetime import datetime, timedelta
from configparser import ConfigParser
from typing import Sequence, List


class InvalidConfigException(Exception):
    pass


class WeathervaneConfigParser(ConfigParser):
    DEFAULT_STATIONS = [6260, 6370]

    def __init__(self):
        super(WeathervaneConfigParser, self).__init__()

    def parse_bit_packing_section(self) -> List[dict]:
        bit_numbers = self.options('Bit Packing')
        bit_numbers = sorted([int(n) for n in bit_numbers])

        bits = []
        for bit_number in bit_numbers:
            bit_config = self.get('Bit Packing', str(bit_number))
            bit_config = bit_config.split(',')
            if len(bit_config) == 2:
                bits.append({
                    'key': bit_config[0],
                    'length': bit_config[1]
                })
            elif len(bit_config) == 5:
                bits.append({
                    'key': bit_config[0],
                    'length': bit_config[1],
                    'min': bit_config[2],
                    'max': bit_config[3],
                    'step': bit_config[4]
                })
            else:
                raise InvalidConfigException("")
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
        bits: List[dict] = self.parse_bit_packing_section()

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
        logging.info(f'Configuration: {configuration}')
        return configuration


class BuienradarParser(object):
    DERIVED_FIELDS = ['error', 'DUMMY_BYTE', 'barometric_trend', 'data_from_fallback', 'random', 'service_byte']
    TREND_MAPPING = {
        -1: 2,
        0: 4,
        1: 1
    }

    def __init__(self, *args, **kwargs):
        self.fallback_used = None
        self.stations = kwargs.get('stations', None)
        self.bits = kwargs.get('bits', None)

    def parse(self, data: str) -> dict:
        raw_weather_data = json.loads(data)
        raw_stations_weather_data = self._to_dict(
            raw_weather_data['actual']['stationmeasurements']
        )
        raw_primary_station_data = self.merge(raw_stations_weather_data, self.stations, self.bits)
        station_weather_data = self.enrich(raw_primary_station_data)

        return station_weather_data

    @staticmethod
    def enrich(weather_data: dict) -> dict:
        weather_data['barometric_trend'] = 4

        weather_data_timestamp = datetime.fromisoformat(weather_data['timestamp'])
        time_delta = abs(datetime.now() - weather_data_timestamp)
        if time_delta > timedelta(hours=2):
            logging.warning(f"{weather_data['timestamp']} is more than {time_delta.hours} hours out of date")
            weather_data['error'] = True
        return weather_data

    @staticmethod
    def merge(weather_data: dict, stations: list, required_fields: Sequence[dict]) -> dict:
        primary_station = stations[0]
        weather_data[primary_station]['data_from_fallback'] = False
        weather_data[primary_station]['error'] = False
        assert primary_station
        secondary_stations = stations[1:]
        if not secondary_stations:
            return weather_data[primary_station]
        for field_dict in required_fields:
            field_name = field_dict['key']
            value = weather_data[primary_station].get(field_name, None)
            if value is None and field_name not in BuienradarParser.DERIVED_FIELDS:
                for secondary_station in secondary_stations:
                    try:
                        fallback_data = weather_data.get(secondary_station, {})[field_name]
                        weather_data[primary_station][field_name] = fallback_data
                        weather_data[primary_station]['data_from_fallback'] = True
                        logging.info(f'Setting fallback, because {field_name} is missing')
                        break
                    except KeyError:
                        continue
                else:
                    logging.warning(f'No backup value found for {field_name}')
                    weather_data[primary_station]['error'] = True
        return weather_data[primary_station]

    @staticmethod
    def _to_dict(stations_weather_data: dict) -> dict:
        return {station_data['stationid']: station_data for station_data in stations_weather_data}
