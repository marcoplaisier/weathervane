import argparse
import logging
import logging.handlers
from multiprocessing import Process, Pipe
from time import sleep
from weatherdata.datasources import BuienradarSource, KNMISource, RijkswaterstaatSource, TestSource
from interfaces.weathervaneinterface import WeatherVaneInterface


class WeatherVane(object):
    def get_source(self, source):
        if source == 'buienradar':
            return BuienradarSource()
        elif source == 'knmi':
            return KNMISource()
        elif source == 'rijkswaterstaat':
            return RijkswaterstaatSource()
        elif source == 'test':
            return TestSource()
        else:
            raise NameError('Data provider not found')

    def main(self, interval, source='buienradar', station_id=6323):
        logging.info("Starting operation")
        interface = WeatherVaneInterface(channel=0, frequency=250000)
        logging.debug("Using " + str(interface))
        weather_data = {'wind_direction': None, 'wind_speed': None, 'wind_speed_max': None, 'air_pressure': None}

        data_source = self.get_source(source)

        pipe_end_1, pipe_end_2 = Pipe()
        counter = 0

        while True:
            if (counter % interval) == 0:
                counter = 0
                p = Process(target=data_source.get_data, args=(pipe_end_1, station_id))
                p.start()

            if pipe_end_2.poll(0):
                weather_data = pipe_end_2.recv()
                logging.info("Received data:" + str(weather_data))

            interface.send(weather_data)

            counter += 1
            sleep(1)

    def set_logger(self):
        weathervane_logger = logging.getLogger('')
        weathervane_logger.setLevel(logging.DEBUG)
        handler = logging.handlers.TimedRotatingFileHandler(filename="weathervane.log",
                                                        when="midnight",
                                                        interval=1,
                                                        backupCount=7)
        formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(module)s:%(message)s")
        handler.setFormatter(formatter)
        weathervane_logger.addHandler(handler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get weather data from a provider and send it through SPI")
    parser.add_argument('-t', '--test', action='store_true', default=False, help="run the program in test mode")
    parser.add_argument('-i', '--interval', action='store', type=int, default=300,
                        help="specify the interval (in seconds) when the weather data is retrieved")
    parser.add_argument('-s', '--station', action='store', type=int, default=6323,
                        help="the id of the the weather station from which the weather data is retrieved")
    parser.add_argument('list', help="return all known weather stations from the given provider")
    parser.add_argument('-p', '--provider', choices=['buienradar', 'knmi', 'rijkswaterstaat'],
                        help='select the provider')
    args = parser.parse_args()

    wv = WeatherVane()
    wv.set_logger()
    wv.main(interval=args.interval, source=args.provider, station_id=args.station)
