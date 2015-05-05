import ConfigParser
import datetime
from BeautifulSoup import BeautifulSoup


class WeathervaneConfigParser(ConfigParser.SafeConfigParser):
    def parse_bit_packing_section(self):
        bit_numbers = self.options('Bit Packing')

        bits = {}
        for bit_number in bit_numbers:
            bit_config = self.get('Bit Packing', bit_number).split(',')
            if len(bit_config) == 2:
                bits[bit_number] = {
                    'key': bit_config[0],
                    'length': bit_config[1]
                }
            else:
                bits[bit_number] = {
                    'key': bit_config[0],
                    'length': bit_config[1],
                    'min': bit_config[2],
                    'max': bit_config[3],
                    'step': bit_config[4]
                }
        return bits

    def parse_station_numbers(self):
        station_numbers = self.options('Stations')

        station_config = {}
        for number in station_numbers:
            try:
                number = int(number)
                station_config[number] = self.get('Stations', str(number))
            except ValueError:
                if number not in ['fallback', 'pins']:
                    logging.debug("Option not recognized")
        return station_config

    def parse_config(self):
        """Takes a configuration parser and returns the configuration as a dictionary

        @param cp:
        @return:
        """
        pins = map(int, self.get('Stations', 'pins').split(','))
        station_config = self.parse_station_numbers()
        bits = self.parse_bit_packing_section()

        configuration = {
            'extended-error-mode': self.getboolean('General', 'extended-error-mode'),
            'channel': self.getint('SPI', 'channel'),
            'frequency': self.getint('SPI', 'frequency'),
            'library': self.get('SPI', 'library'),
            'interval': self.getint('General', 'interval'),
            'source': self.get('General', 'source'),
            'fallback-station': self.get('Stations', 'fallback'),
            'stations': {
                'pins': pins,
                'config': station_config
            },
            'bits': bits
        }
        return configuration


class BuienradarParser(object):
    INVALID_DATA = ['0', 0, '-', '', None]
    FIELD_MAPPING = {
        'wind_direction': 'windrichtingGR',
        'wind_speed': 'windsnelheidMS',
        'wind_speed_max': 'windstotenMS',
        'wind_speed_bft': 'windsnelheidBF',
        'air_pressure': 'luchtdruk',
        'temperature': 'temperatuurGC',
        'wind_chill': 'wind_chill',
        'humidity': 'luchtvochtigheid',
        'station_name': 'stationnaam',
        'latitude': 'lat',
        'longitude': 'lon',
        'date': 'datum',
        'wind_direction_code': 'windrichting',
        'sight_distance': 'zichtmeters',
        'rain_mm_per_hour': 'regenMMPU',
        'temperature_10_cm': 'temperatuur10cm'
    }

    def __init__(self, data, fallback=6310, *args, **kwargs):
        self.soup = BeautifulSoup(data)
        self.fallback = fallback

    def get_date(self, station_id):
        date = self.get_data_from_station(station_id, 'datum')
        return datetime.datetime.strptime(date, '%d/%m/%Y %H:%M:%S')

    def get_data_from_station(self, station_id, field_name):
        station_data = self.soup.find("weerstation", id=station_id).find(field_name.lower())

        if station_data is None:
            return station_data
        else:
            return station_data.string

    def get_station_codes(self):
        code_tags = self.soup("stationcode")
        codes = [int(tag.string) for tag in code_tags]
        return codes

    def get_station_name_by_id(self, station_id):
        return self.get_data_from_station(station_id, "stationnaam")

    def get_wind_direction_degrees(self, station_id):
        data = self.get_data_from_station(station_id, "windrichtinggr")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "windrichtinggr")
        return float(data)

    def get_wind_speed(self, station_id):
        data = self.get_data_from_station(station_id, "windsnelheidms")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "windsnelheidms")
        return float(data)

    def get_wind_direction(self, station_id):
        data = self.get_data_from_station(station_id, "windrichting")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "windrichting")
        return data

    def get_air_pressure(self, station_id):
        data = self.get_data_from_station(station_id, "luchtdruk")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "luchtdruk")
        return float(data)

    def get_wind_maximum(self, station_id):
        data = self.get_data_from_station(station_id, "windstotenms")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "windstotenms")
        return float(data)

    def get_temperature(self, station_id):
        data = self.get_data_from_station(station_id, "temperatuurGC")
        if data in self.INVALID_DATA:
            data = self.get_data_from_station(self.fallback, "temperatuurGC")
        return float(data)

    def get_wind_chill(self, station_id):
        wind_speed = self.get_wind_speed(station_id)
        temperature = self.get_temperature(station_id)
        return calculate_wind_chill(wind_speed, temperature)


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


def calculate_wind_chill(wind_speed, temperature):
    return 13.12 + 0.6215 * temperature - 13.96 * wind_speed ** 0.16 + 0.4867 * temperature * wind_speed**0.16