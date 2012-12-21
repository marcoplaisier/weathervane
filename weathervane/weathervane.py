from __future__ import division
import argparse
from time import sleep
from urllib2 import urlopen
from interfaces.weathervaneinterface import WeatherVaneInterface
from parser.parser import BuienradarParser
import gc 

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
        interface = WeatherVaneInterface(0, 250000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter%255, (255-counter)%255, test, 0]
            interface.send(data)
            sleep(0.1)

    def main(self, station_id=6323):
        interface = WeatherVaneInterface(0, 250000)

        counter = 0

        while True:
            if counter % 300 == 0:
                print 'fetching data'
                response = urlopen("http://xml.buienradar.nl")
                data = response.read()
                parser = BuienradarParser(data)
                wind = parser.get_wind_speed(station_id)%64
                wind_direction = parser.get_station_wind_direction(station_id)/22.5
                air_pressure = parser.get_air_pressure(station_id)-900
                del response
                del parser
                del data

            interface.send([int(wind), int(wind_direction), int(air_pressure), 0])
            counter += 1
            sleep(0.5)

if __name__ == "__main__":
    gc.set_debug(gc.DEBUG_STATS)
    parser = argparse.ArgumentParser(description="TBD")
    parser.add_argument('-t', '--test', action='store_true',
    default=False, help="run the program in test mode")
    wv = WeatherVane()

    args = parser.parse_args()
    if args.test:
        wv.test_mode()
    else:
        wv.main()
