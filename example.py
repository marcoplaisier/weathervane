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
     'stations': {0: '6320',
                  1: '6321',
                  2: '6310',
                  3: '6312',
                  4: '6308',
                  5: '6311',
                  6: '6331',
                  7: '6316'}
     }

with open(os.path.join(os.getcwd(), 'tests', 'buienradar.xml'), 'rU') as f:
    data = f.read()
    bp = BuienradarParser(**a)
    wd = bp.parse(raw_xml=data, **a)

print(wd)

bits = a['bits']
fmt = ''
for i, data in enumerate(bits):
    formatting = bits[str(i)]
    s = "hex:{0}, ".format(formatting['length'])
    fmt += s
hexstring = fmt[:-1]
import bitstring

result = {}
index = 0
for key, value in list(bits.items()):
    fmt = value
    value = wd.get(fmt['key'], 0)
    if type(value) != str:
        value -= float(fmt.get('min', 0))
        value /= float(fmt.get('step', 1))
        value = int(value)
    else:
        value = WeatherVaneInterface.WIND_DIRECTIONS[value]
    result[fmt['key']] = value
    index += 1
