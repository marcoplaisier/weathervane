from __future__ import division
import argparse
from multiprocessing import Lock, Process, Pipe
from time import sleep
import os
from interfaces.testinterface import TestInterface
from interfaces.weathervaneinterface import WeatherVaneInterface
from weathervane.datasources import BuienradarSource

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
        interface = TestInterface(channel=0, frequency=25000)
        counter = 0

        while True:
            counter += 1
            if counter % 2:
                test = 0x55
            else:
                test = 0xAA

            data = [counter%255, (255-counter)%255, test]
            print data
            interface.send(data)
            sleep(1)

    def main(self, station_id=6323):
        interface = WeatherVaneInterface(channel=0, frequency=250000)
        weather_data = {'wind_direction': None, 'wind_speed': None, 'wind_speed_max': None, 'air_pressure': None}
        data_source = BuienradarSource()
        pipe_end_1, pipe_end_2 = Pipe()
        l = Lock()
        counter = 0

        while True:
            if counter % 300 == 0:
                counter = 0
                p = Process(target=data_source.get_data, args=(pipe_end_1, station_id))
                p.start()

            if pipe_end_2.poll():
                weather_data = pipe_end_2.recv()
                p.join()

            interface.send(weather_data)
            print weather_data

            counter += 1
            sleep(1)

if __name__ == "__main__":
    #gc.set_debug(gc.DEBUG_STATS)
    os.system("gpio load spi")
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
