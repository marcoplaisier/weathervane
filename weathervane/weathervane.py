from __future__ import division
import argparse
from time import sleep
from urllib2 import urlopen
from interfaces.weathervaneinterface import WeatherVaneInterface
from weatherdata.weatherdata import BuienradarParser

class WeatherVane(object):

    def test_mode(self):
        """
        Test mode is used to output a predicable sequence of bytes to
        the output pins.
        The program will send 3 bytes every second to the pins.
        - Byte 1: an increasing counter (modulo 255)
        - Byte 2: a decreasing counter (idem)
        - Byte 3: switches between 0x55 and 0xAA

        """
        interface = WeatherVaneInterface(channel=0, frequency=25000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter%255, (255-counter)%255, test]
            interface.send(data)
            sleep(1)

    def main(self, station_id=6323):
        interface = WeatherVaneInterface(channel=0, frequency=250000)

        counter = 0

        while True:
            if counter % 300 == 0:
                counter = 0
                print 'fetching data'

                response = urlopen("http://xml.buienradar.nl")
                data = response.read()
                parser = BuienradarParser(data)

                wind_speed = parser.get_wind_speed(station_id)
                wind_direction = parser.get_wind_direction(station_id)
                air_pressure = parser.get_air_pressure(station_id)

                del response
                del parser
                del data

            weather_data = {'wind_direction': wind_direction, 'wind_speed': wind_speed, 'air_pressure': air_pressure}
            interface.send(weather_data)
            counter += 1
            sleep(1)

if __name__ == "__main__":
    #gc.set_debug(gc.DEBUG_STATS)

    parser = argparse.ArgumentParser(description="TBD")
    parser.add_argument('-t', '--test',
                        action='store_true',
                        default=False,
                        help="run the program in test mode")
    wv = WeatherVane()

    args = parser.parse_args()
    if args.test:
        wv.test_mode()
    else:
        wv.main()
