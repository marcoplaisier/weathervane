import logging
import os
import time

import requests

from weathervane.parser import BuienradarParser

HTTP_OK = 200

DEFAULT_WEATHER_DATA = {
    "error": True,
    "airpressure": 900,
    "humidity": 0,
    "rain": True,
    "random": 0,
    "temperature": -39.9,
    "groundtemperature": -39.9,
    "feeltemperature": 0,
    "winddirection": "N",
    "winddirectiondegrees": 0,
    "windspeed": 0,
    "windgusts": 0,
    "windspeedBft": 0,
}


def get_weather_string_with_retries(max_retries=5, retry_interval=5):
    while max_retries > 0:
        try:
            r = requests.get("https://data.buienradar.nl/2.0/feed/json", timeout=10)

            if r.status_code == HTTP_OK:
                logging.info(f"Weather data retrieved in {r.elapsed} ms")
                return r.text
            else:
                logging.warning(f"Got response, but unhandled status code {r.status_code}")

        except (ConnectionError, TimeoutError) as e:
            if max_retries > 0:
                logging.error(e)
                max_retries -= 1
                retry_interval *= 2
                if max_retries == 1:
                    # if this is the last attempt, then attempt to get a new IP address.
                    logging.info("Attempting to reset the internet connection")
                    os.system("sudo /etc/init.d/networking restart")
                    time.sleep(15)
                else:
                    logging.warning(f"Retrieving data failed. Retrying after {retry_interval} seconds")
                    time.sleep(retry_interval)
            else:
                return None
    return None


def fetch_weather_data(conn, *args, **kwargs):
    data = get_weather_string_with_retries()

    if data:
        bp = BuienradarParser(*args, **kwargs)
        try:
            wd = bp.parse(data)
        except Exception as e:
            logging.error("Data parsing failed. Cannot send good data. Setting error.")
            wd = DEFAULT_WEATHER_DATA
    else:
        logging.error("Retrieving data failed several times. Setting error.")
        wd = DEFAULT_WEATHER_DATA

    conn.send(wd)
    conn.close()
