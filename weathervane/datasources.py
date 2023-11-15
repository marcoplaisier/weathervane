import logging

import requests
from tenacity import retry, wait_random_exponential, stop_after_delay

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

logger = logging.getLogger('weathervane.parser')


@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_delay(300))
def get_weather_string_with_retries():
    r = requests.get("https://data.buienradar.nl/2.0/feed/json", timeout=5)

    if r.status_code == HTTP_OK:
        logger.info(f"Weather data retrieved in {r.elapsed} ms")
        return r.text
    else:
        logger.warning(f"Got response in {r.elapsed} ms, but unhandled status code {r.status_code}")
        raise ConnectionError(f"Buienradar: {r.status_code}")


def fetch_weather_data(conn, *args, **kwargs):
    data = get_weather_string_with_retries()

    if data:
        bp = BuienradarParser(*args, **kwargs)
        try:
            wd = bp.parse(data)
        except Exception as e:
            logger.error("Data parsing failed. Cannot send good data. Setting error.")
            wd = DEFAULT_WEATHER_DATA
    else:
        logger.error("Retrieving data failed several times. Setting error.")
        wd = DEFAULT_WEATHER_DATA

    conn.send(wd)
    conn.close()
