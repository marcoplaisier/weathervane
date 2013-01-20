from urllib2 import urlopen
from .weatherdata.parser import BuienradarParser

class BuienradarSource(object):
    def get_data(self, conn, station_id):
        response = urlopen("http://xml.buienradar.nl")
        data = response.read()

        parser = BuienradarParser(data)

        wind_speed = parser.get_wind_speed(station_id)
        wind_direction = parser.get_wind_direction(station_id)
        air_pressure = parser.get_air_pressure(station_id)
        wind_speed_max = parser.get_wind_maximum(station_id)

        weather_data = {'wind_direction': wind_direction, 'wind_speed': wind_speed,
                        'wind_speed_max': wind_speed_max, 'air_pressure': air_pressure}

        conn.send(weather_data)
        conn.close()