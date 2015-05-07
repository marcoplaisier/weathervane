from urllib2 import urlopen
from parser import BuienradarParser


def retrieve_xml(url):
    response = urlopen(url)
    data = response.read()
    return data


def fetch_weather_data(conn, station_id, *args, **kwargs):
    data = retrieve_xml("http://xml.buienradar.nl")
    wd = BuienradarParser.parse(data, station_id, **kwargs)

    conn.send(wd)
    conn.close()