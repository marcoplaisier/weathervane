import logging
from urllib2 import urlopen, URLError, HTTPError

from weathervane.parser import BuienradarParser


class DataSourceError(RuntimeError):
    pass


def retrieve_xml(url):
    try:
        response = urlopen(url)
        data = response.read()
    except HTTPError:
        raise DataSourceError('HTTP Error: Data connection failed')
    except URLError:
        raise DataSourceError('URL Error: Data connection failed')
    return data


def fetch_weather_data(conn, station_id, *args, **kwargs):
    bp = BuienradarParser()
    try:
        data = retrieve_xml("http://xml.buienradar.nl")
        wd = bp.parse(data, station_id, *args, **kwargs)
    except DataSourceError:
        logging.error('Problem with data collection')
        wd = {
            'error': True,
            'air_pressure': 900,
            'humidity': 0,
            'rain': True,
            'random': 0,
            'temperature': -39.9,
            'temperature_10_cm': -39.9,
            'wind_chill': 0,
            'wind_direction': 'N',
            'wind_direction_code': 'N',
            'wind_direction_degrees': 0,
            'wind_speed': 0,
            'wind_speed_max': 0,
            'wind_speed_bft': 0
        }

    conn.send(wd)
    conn.close()