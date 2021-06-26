import logging
import os
import time

import requests

from weathervane.parser import BuienradarParser

DEFAULT_WEATHER_DATA = {
    'error': True,
    'airpressure': 900,
    'humidity': 0,
    'rain': True,
    'random': 0,
    'temperature': -39.9,
    'groundtemperature': -39.9,
    'feeltemperature': 0,
    'winddirection': 'N',
    'winddirectiondegrees': 0,
    'windspeed': 0,
    'windgusts': 0,
    'windspeedBft': 0
}


def get_weather_string_with_retries(max_retries=5, retry_interval=5):
    while max_retries > 0:
        try:
            r = requests.get("https://data.buienradar.nl/2.0/feed/json", timeout=10)
            if r.status_code == 200:
                logging.info('Weather data retrieved in {} ms'.format(r.elapsed))
                return r.text
            else:
                logging.warning('Got response, but unhandled status code {}'.format(r.status_code))
        except (ConnectionError, TimeoutError):
            if max_retries > 0:
                logging.warning('Retrieving data failed. Retrying after {} seconds'.format(retry_interval))
                time.sleep(retry_interval)
                max_retries -= 1
                retry_interval *= 2
            if max_retries == 2:
                # if it still doesn't work, then attempt to get a new IP address. Maybe it is the Internet connection
                logging.info('Attempting to reset the internet connection')
                os.system('sudo /etc/init.d/networking restart')
    return None


def fetch_weather_data(conn, *args, **kwargs):
    data = get_weather_string_with_retries()

    if data:
        bp = BuienradarParser(*args, **kwargs)
        try:
            wd = bp.parse(data)
        except:
            logging.error('Data parsing failed. Cannot send good data. Setting error.')
            wd = DEFAULT_WEATHER_DATA
    else:
        logging.error('Retrieving data failed several times. Setting error.')
        wd = DEFAULT_WEATHER_DATA

    conn.send(wd)
    conn.close()
