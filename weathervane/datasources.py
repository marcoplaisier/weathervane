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
    data = retrieve_xml("http://xml.buienradar.nl")
    bp = BuienradarParser()
    wd = bp.parse(data, station_id, *args, **kwargs)

    conn.send(wd)
    conn.close()