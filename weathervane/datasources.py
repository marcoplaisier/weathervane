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
    if not kwargs.get('test', False):
        data = retrieve_xml("http://xml.buienradar.nl")
    else:
        with file(os.path.join(os.getcwd(), 'tests', 'buienradar.xml'), 'rU') as f:
            data = f.read()

    bp = BuienradarParser()
    wd = bp.parse(data, station_id, *args, **kwargs)

    conn.send(wd)
    conn.close()