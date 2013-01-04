from __future__ import division
import argparse
from time import sleep
from urllib2 import urlopen
from interfaces.weathervaneinterface import WeatherVaneInterface
from weatherdata.weatherdata import BuienradarParser

class WeatherVane(object):
    wind_directions = {'N': 0x00, 'NNO': 0x01, 'NO': 0x02, 'ONO': 0x03,
                       'O': 0x04, 'OZO': 0x05, 'ZO': 0x06, 'ZZO': 0x07,
                       'Z': 0x08, 'ZZW': 0x09, 'ZW': 0x0A, 'WZW': 0x0B,
                       'W': 0x0C, 'WNW': 0x0D, 'NW': 0x0E, 'NNW': 0x0F}
    AIR_PRESSURE_OFFSET = 900
    WIND_SPEED_SELECTOR = 127

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
                wind = parser.get_wind_speed(station_id) & self.WIND_SPEED_SELECTOR
                wind_direction_code = parser.get_wind_direction(station_id)
                wind_direction = self.wind_directions[wind_direction_code]
                air_pressure = parser.get_air_pressure(station_id) - self.AIR_PRESSURE_OFFSET

                del response
                del parser
                del data

            interface.send([int(wind_direction), int(wind), int(air_pressure)])
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
