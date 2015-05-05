from urllib2 import urlopen
from parser import BuienradarParser


def retrieve_xml(self, url):
    response = urlopen(url)
    data = response.read()
    return data


def fetch_weather_data(self, conn, station_id, *args, **kwargs):
    data = retrieve_xml("http://xml.buienradar.nl")
    wd = BuienradarParser.parse(data, *args, **kwargs)

    conn.send(wd)
    conn.close()