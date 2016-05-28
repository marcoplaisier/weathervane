import logging
from urllib.request import urlopen
from urllib.error import URLError, HTTPError

from weathervane.parser import BuienradarParser


class DataSourceError(RuntimeError):
    pass


def retrieve_xml(url):
    try:
        response = urlopen(url)
        data = response.read()
    except HTTPError as e:
        logging.error('HTTP Error')
        raise DataSourceError('HTTP Error: Data connection failed', e)
    except URLError as e:
        logging.error('URL Error')
        raise DataSourceError('URL Error: Data connection failed', e)
    return data


def fetch_weather_data(conn, station_id, *args, **kwargs):
    bp = BuienradarParser()
    try:
        data = retrieve_xml("http://xml.buienradar.nl")
        wd = bp.parse(data, station_id, *args, **kwargs)
    except DataSourceError as e:
        logging.error('Problem with data collection')
        wd = {
            'error': True,
            'air_pressure': 900,
            'humidity': 0,
            'rain': True,
            'random': 0,
            'temperature': -39.9,
            'temperature_10_cm': -39.9,
            'apparent_temperature': 0,
            'wind_direction': 'N',
            'wind_direction_code': 'N',
            'wind_direction_degrees': 0,
            'wind_speed': 0,
            'wind_speed_max': 0,
            'wind_speed_bft': 0
        }
    conn.send(wd)
    conn.close()