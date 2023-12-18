import logging.handlers
from datetime import datetime

import requests
from pythonjsonlogger import jsonlogger
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


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            # this doesn't use record.created, so it is slightly off
            now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname


logger = logging.getLogger("weathervane.datasource")
logger.setLevel(logging.INFO)
handler = logging.handlers.TimedRotatingFileHandler(
    filename="datasource.log", when="midnight", interval=1, backupCount=1
)
stream_handler = logging.StreamHandler()
formatter = CustomJsonFormatter('%(timestamp)s %(level)s %(name)s %(message)s')
stream_handler.setFormatter(formatter)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.addHandler(stream_handler)


@retry(wait=wait_random_exponential(multiplier=1, max=60), stop=stop_after_delay(300))
def get_weather_string_with_retries():
    logger.info("Starting request to buienradar")
    r = requests.get("https://data.buienradar.nl/2.0/feed/json", timeout=5)
    logger.info("Request done")
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
