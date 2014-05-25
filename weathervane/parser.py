from BeautifulSoup import BeautifulSoup
import datetime


class BuienradarParser(object):
    INVALID_DATA = ['0', 0, '-', '', None]

    def __init__(self, data):
        self.soup = BeautifulSoup(data)

    def get_date(self, station_id):
        date = self.get_data_from_station(station_id, 'datum')
        return datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')

    def get_data_from_station(self, station_id, field_name):
        station_data = self.soup.find("weerstation", id=station_id).find(field_name)

        if station_data is None:
            return station_data
        else:
            return station_data.string

    def get_station_codes(self):
        code_tags = self.soup("stationcode")
        codes = [tag.string for tag in code_tags]
        return codes

    def get_station_name_by_id(self, station_id):
        return self.get_data_from_station(station_id, "stationnaam")

    def get_wind_direction_degrees(self, station_id):
        data = self.get_data_from_station(station_id, "windrichtinggr")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(6310, "windrichtinggr")
        return data

    def get_wind_speed(self, station_id):
        data = self.get_data_from_station(station_id, "windsnelheidms")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(6310, "windsnelheidms")
        return data

    def get_wind_direction(self, station_id):
        data = self.get_data_from_station(station_id, "windrichting")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(6310, "windrichting")
        return data

    def get_air_pressure(self, station_id):
        data = self.get_data_from_station(station_id, "luchtdruk")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(6310, "luchtdruk")
        return data

    def get_wind_maximum(self, station_id):
        data = self.get_data_from_station(station_id, "windstotenms")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(6310, "windstotenms")
        return data


class KNMIParser(object):
    WEATHER_STATIONS = {210: 'Valkenburg', 225: 'IJmuiden', 235: 'De Kooy', 240: 'Schiphol', 242: 'Vlieland',
                        249: 'Berkhout', 251: 'Terschelling', 257: 'Wijk aan Zee', 260: 'De Bilt',
                        265: 'Soesterberg', 267: 'Stavoren', 269: 'Lelystad', 270: 'Leeuwarden', 273: 'Marknesse',
                        275: 'Deelen', 277: 'Lauwersoog', 278: 'Heino', 279: 'Hoogeveen', 280: 'Eelde', 283: 'Hupsel',
                        286: 'Nieuw Beerta',  290: 'Twenthe', 310: 'Vlissingen', 319: 'Westdorpe',
                        323: 'Wilhelminadorp', 330: 'Hoek van Holland', 340: 'Woensdrecht', 344: 'Rotterdam',
                        348: 'Cabauw', 350: 'Gilze-Rijen', 356: 'Herwijnen', 370: 'Eindhoven', 375: 'Volkel',
                        377: 'Ell', 380: 'Maastricht AP', 391: 'Arcen', 0: 'Houtribdijk'}

    DATA_COLUMNS = {'station_name': 0, 'weather_description': 1, 'temperature': 2, 'chill': 3, 'relative_humidity': 4,
                    'wind_direction': 5, 'wind_speed': 6, 'sight_distance': 7, 'air_pressure': 8}

    def __init__(self, data):
        self.soup = BeautifulSoup(data)
        weather_data_html = self.soup.find('table', {'class': 'realtable'}).findAll('tr')

        self.data = {}
        for station_data_html in weather_data_html[1:]:  # First row contains heading and is skipped
            measurements_html = station_data_html.findAll('td')

            station_data = {}
            for field_name, field_name_id in self.DATA_COLUMNS.items():
                measurement_text = measurements_html[field_name_id].renderContents()
                measurement_data = self.__clean(measurement_text)
                station_data[field_name] = measurement_data

            for station_id, station_name in self.WEATHER_STATIONS.items():
                if station_name == station_data['station_name']:
                    self.data[station_id] = station_data
            else:
                pass

    def __clean(self, data):
        result = data.replace('&nbsp;', '').strip()

        if result == '':
            return None
        else:
            return result

    def get_date(self, station_id):
        pass

    def get_data_from_station(self, station_id, field_name):
        return self.data[station_id][field_name]

    def get_station_codes(self):
        return self.WEATHER_STATIONS.keys()

    def get_station_name_by_id(self, station_id):
        return self.WEATHER_STATIONS[station_id]

    def get_wind_direction_degrees(self, station_id):
        return None

    def get_wind_speed(self, station_id):
        return int(self.get_data_from_station(station_id, 'wind_speed'))

    def get_wind_direction(self, station_id):
        return self.get_data_from_station(station_id, 'wind_direction')

    def get_air_pressure(self, station_id):
        air_pressure = self.get_data_from_station(station_id, 'air_pressure')
        if air_pressure is None:
            return None
        else:
            return float(air_pressure)

    def get_wind_maximum(self, station_id):
        return None