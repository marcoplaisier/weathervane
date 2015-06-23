import os
from urllib2 import urlopen, URLError, HTTPError

from weathervane.parser import BuienradarParser


class DataSourceError(RuntimeError):
    pass


def retrieve_xml(url):
    response = urlopen(url)
    data = response.read()
    return data


def fetch_weather_data(conn, station_id, *args, **kwargs):
    bp = BuienradarParser()

    if kwargs.get('test', False):
        path_to_test_data = os.path.join(os.getcwd(), 'tests', 'buienradar.xml')
        with file(path_to_test_data, 'r') as f:
            data = f.read()
        wd = bp.parse(data, station_id, *args, **kwargs)
    else:
        data = retrieve_xml("http://xml.buienradar.nl")
        wd = bp.parse(data, station_id, *args, **kwargs)

    conn.send(wd)
    conn.close()