from BeautifulSoup import BeautifulSoup
from urllib2 import urlopen
import re

class BuienRadarParser:
    def __init__(self, data):
        self.soup = BeautifulSoup(data)

    def get_data_from_station(self, station_id, fieldname):
        station_data = self.soup.find("weerstation", id=station_id).find(fieldname)
        return station_data 

    def get_station_codes(self):
        codetags = self.soup("stationcode")
        codes = [tag.string for tag in codetags]
        return codes

    def get_station_name_by_id(self, number):
        station_name = self.get_data_from_station(number, "stationnaam")
        return station_name

    def get_station_windrichting(self, number):
        windrichting = self.get_data_from_station(number, "windrichtinggr")
        return windrichting

if __name__ == "__main__":
    response = urlopen("http://xml.buienradar.nl")
    data = response.read()
    wb = BuienRadarParser(data)
    codes = wb.get_station_codes()
    print codes
    name = wb.get_station_name_by_id(id)
    wind = wb.get_station_windrichting(id)
    print name.string, wind.string
