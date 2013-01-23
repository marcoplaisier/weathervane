from urllib2 import urlopen
from parser import BuienradarParser

class DataSource():
    def get_data(self, conn, station_id):
        raise NotImplementedError("Do not use this interface directly, but subclass it and add your own functionality")

    def fetch_weather_data(self, url):
        response = urlopen(url)
        data = response.read()
        return data

class BuienradarSource(DataSource):
    def get_data(self, conn, station_id):
        data = self.fetch_weather_data("http://xml.buienradar.nl")
        parser = BuienradarParser(data)

        wind_speed = parser.get_wind_speed(station_id)
        wind_direction = parser.get_wind_direction(station_id)
        air_pressure = parser.get_air_pressure(station_id)
        wind_speed_max = parser.get_wind_maximum(station_id)

        weather_data = {'wind_direction': wind_direction, 'wind_speed': wind_speed,
                        'wind_speed_max': wind_speed_max, 'air_pressure': air_pressure}

        conn.send(weather_data)
        conn.close()

class KNMISource(object):
    pass

class RijkswaterstaatSource(object):
    pass