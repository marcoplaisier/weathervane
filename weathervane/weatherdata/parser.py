from BeautifulSoup import BeautifulSoup
import datetime

class BuienradarParser(object):
    def __init__(self, data):
        self.soup = BeautifulSoup(data)

    def get_date(self, station_id):
        date = self.get_data_from_station(station_id, 'datum')
        return datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')

    def get_data_from_station(self, station_id, fieldname):
        station_data = self.soup.find("weerstation", id=station_id).find(fieldname)
        return station_data.string

    def get_station_codes(self):
        code_tags = self.soup("stationcode")
        codes = [tag.string for tag in code_tags]
        return codes

    def get_station_name_by_id(self, station_id):
        station_name = self.get_data_from_station(station_id, "stationnaam")
        return station_name

    def get_wind_direction_degrees(self, station_id):
        wind_direction = self.get_data_from_station(station_id, "windrichtinggr")
        return float(wind_direction)

    def get_wind_speed(self, station_id):
        wind_speed = self.get_data_from_station(station_id, "windsnelheidms")
        return float(wind_speed)

    def get_wind_direction(self, station_id):
        wind_direction = self.get_data_from_station(station_id, "windrichting")
        assert isinstance(wind_direction, basestring)
        return wind_direction

    def get_air_pressure(self, station_id):
        air_pressure = self.get_data_from_station(station_id, "luchtdruk")
        return float(air_pressure)

    def get_wind_maximum(self, station_id):
        wind_speed_max = self.get_data_from_station(station_id, "windstotenMS")
        return float(wind_speed_max)