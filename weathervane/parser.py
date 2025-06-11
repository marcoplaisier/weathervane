import logging

from configparser import ConfigParser
from datetime import datetime
from typing import List, Sequence

HOUR_ERROR_LIMIT = 2.0 * 60 * 60

SIMPLE_CONFIG = 2
EXTENDED_CONFIG = 5

logger = logging.getLogger()


class InvalidConfigException(Exception):
    pass


class WeathervaneConfigParser(ConfigParser):
    DEFAULT_STATIONS = [6260, 6370]
    KEY_INDEX = 0
    LENGTH_INDEX = 1
    MIN_INDEX = 2
    MAX_INDEX = 3
    STEP_INDEX = 4

    def __init__(self):
        super(WeathervaneConfigParser, self).__init__()

    def parse_bit_packing_section(self) -> List[dict]:
        bit_numbers = self.options("Bit Packing")
        bit_numbers = sorted([int(n) for n in bit_numbers])

        bits = []
        for bit_number in bit_numbers:
            bit_config = self.get("Bit Packing", str(bit_number))
            bit_config = bit_config.split(",")
            if len(bit_config) == SIMPLE_CONFIG:
                bits.append({"key": bit_config[self.KEY_INDEX], "length": bit_config[self.LENGTH_INDEX]})
            elif len(bit_config) == EXTENDED_CONFIG:
                bits.append(
                    {
                        "key": bit_config[self.KEY_INDEX],
                        "length": bit_config[self.LENGTH_INDEX],
                        "min": bit_config[self.MIN_INDEX],
                        "max": bit_config[self.MAX_INDEX],
                        "step": bit_config[self.STEP_INDEX],
                    }
                )
            else:
                raise InvalidConfigException("")
        return bits

    def parse_station_numbers(self):
        try:
            station_numbers = self["Stations"]
        except KeyError:
            logger.error("Stations sections in config is formatted incorrectly. Using default stations")
            return self.DEFAULT_STATIONS

        stations = []
        station_id = None
        for i in range(len(station_numbers)):
            try:
                station_id = int(self["Stations"][str(i)])
            except KeyError:
                pass
            if station_id:
                stations.append(station_id)
        return stations

    def parse_config(self):
        """Takes a configuration parser and returns the configuration as a dictionary

        @return: configuration as dictionary
        """
        logger.info("Parsing configuration")
        station_config = self.parse_station_numbers()
        bits: List[dict] = self.parse_bit_packing_section()

        configuration = {
            "channel": self.getint("SPI", "channel"),
            "frequency": self.getint("SPI", "frequency"),
            "library": self.get("SPI", "library"),
            "data_collection_interval": self.getint("General", "data_collection_interval"),
            "source": self.get("General", "source"),
            "data_display_interval": float(self.get("General", "data_display_interval")),
            "test": self.getboolean("General", "test"),
            "barometric_trend": self.getboolean("General", "barometric_trend"),
            "stations": station_config,
            "bits": bits,
            "display": {
                "auto-turn-off": self.getboolean("Display", "auto-turn-off"),
                "start-time": self.get("Display", "start-time"),
                "end-time": self.get("Display", "end-time"),
                "pin": self.getint("Display", "pin"),
            },
        }
        logger.info("Configuration successfully parsed")
        return configuration


def is_weather_data_stale(timestamp, now):
    weather_data_ts = datetime.fromisoformat(timestamp).timestamp()
    now_ts = now.timestamp()
    time_delta_in = now_ts - weather_data_ts
    if time_delta_in > HOUR_ERROR_LIMIT:
        logger.error(f"{timestamp} is more than {(time_delta_in/3600):.2f} hours old; data is stale")
        return True
    return False


class BuienradarParser(object):
    DERIVED_FIELDS = [
        "error",
        "DUMMY_BYTE",
        "barometric_trend",
        "data_from_fallback",
        "random",
        "service_byte",
    ]
    TREND_MAPPING = {'dropping': 2, 'stable': 4, 'rising': 1}

    def __init__(self, stations, bits):
        self.fallback_used = None
        self.stations = stations
        self.bits = bits

    def parse(self, data: dict) -> dict:
        raw_stations_weather_data = self._to_dict(
            data["actual"]["stationmeasurements"]
        )
        raw_primary_station_data = self.merge(
            raw_stations_weather_data, self.stations, self.bits
        )
        station_weather_data = self.enrich(raw_primary_station_data)

        return station_weather_data

    @staticmethod
    def enrich(weather_data: dict) -> dict:
        weather_data["barometric_trend"] = BuienradarParser.TREND_MAPPING['stable']
        weather_data["error"] = is_weather_data_stale(weather_data["timestamp"], datetime.now())
        return weather_data

    @staticmethod
    def merge(
            weather_data: dict, stations: list, required_fields: Sequence[dict]
    ) -> dict:
        primary_station = stations[0]
        try:
            weather_data[primary_station]["data_from_fallback"] = False
            secondary_stations = stations[1:]
        except KeyError:
            logger.error(f"Primary station {primary_station} not found in data")
            primary_station = stations[1]
            secondary_stations = stations[1:]
            weather_data[primary_station]["data_from_fallback"] = True

        weather_data[primary_station]["error"] = False

        if not secondary_stations:
            return weather_data[primary_station]
        for field_dict in required_fields:
            field_name = field_dict["key"]
            value = weather_data[primary_station].get(field_name, None)
            if value is None and field_name not in BuienradarParser.DERIVED_FIELDS:
                logger.warning(f"Using data from fallback stations for field {field_name}")
                for secondary_station in secondary_stations:
                    try:
                        fallback_data = weather_data.get(secondary_station, {})[field_name]
                        weather_data[primary_station][field_name] = fallback_data
                        weather_data[primary_station]["data_from_fallback"] = True
                        logger.info(f"Set {field_name} to {fallback_data}, due to missing data at the primary station")
                        break
                    except KeyError:
                        continue
                else:
                    logger.error(f"No backup value found for {field_name}; setting error")
                    weather_data[primary_station]["error"] = True
        return weather_data[primary_station]

    @staticmethod
    def _to_dict(stations_weather_data: dict) -> dict:
        return {
            station_data["stationid"]: station_data
            for station_data in stations_weather_data
        }
