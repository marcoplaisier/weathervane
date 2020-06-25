import json
import os

from weathervane.parser import BuienradarParser
from weathervane.weathervaneinterface import WeatherVaneInterface

a = {'bits': {'0': {'key': 'wind_direction', 'length': '4'},
              '1': {'key': 'wind_speed',
                    'length': '6',
                    'max': '63',
                    'min': '0',
                    'step': '1'},
              '2': {'key': 'wind_speed_max',
                    'length': '6',
                    'max': '63',
                    'min': '0',
                    'step': '1'},
              '3': {'key': 'wind_speed_bft',
                    'length': '4',
                    'max': '12',
                    'min': '1',
                    'step': '1'},
              '4': {'key': 'air_pressure',
                    'length': '8',
                    'max': '1155',
                    'min': '900',
                    'step': '1'},
              '5': {'key': 'temperature',
                    'length': '10',
                    'max': '49.9',
                    'min': '-39.9',
                    'step': '0.1'},
              '6': {'key': 'apparent_temperature',
                    'length': '10',
                    'max': '49.9',
                    'min': '-39.9',
                    'step': '0.1'},
              '7': {'key': 'humidity',
                    'length': '7',
                    'max': '100',
                    'min': '0',
                    'step': '1'},
              '8': {'key': 'service_byte', 'length': '5'},
              '9': {'key': 'DUMMY_BYTE', 'length': '4'}},
     'channel': 0,
     'extended-error-mode': False,
     'frequency': 250000,
     'interval': 300,
     'library': 'wiringPi',
     'source': 'buienradar',
     'stations': [6320, 6321, 6310, 6312, 6308, 6311, 6331, 6316]
     }

file_path = os.path.join(os.getcwd(), 'tests', 'buienradar.json')

with open(file_path, 'r', encoding='utf-8') as f:  # rU opens file with line endings from different platforms correctly
    data = f.read()
    bp = BuienradarParser(**a)
    wd = bp.parse(data=data)

bits = a['bits']
fmt = ''
for i, data in enumerate(bits):
    formatting = bits[str(i)]
    s = "hex:{0}, ".format(formatting['length'])
    fmt += s
hexstring = fmt[:-1]