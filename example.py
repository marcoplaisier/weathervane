import os

from weathervane.parser import BuienradarParser


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
              '6': {'key': 'wind_chill',
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
     'fallback-station': '6310',
     'frequency': 250000,
     'interval': 300,
     'library': 'wiringPi',
     'source': 'buienradar',
     'stations': {'config': {0: '6320',
                             1: '6321',
                             2: '6310',
                             3: '6312',
                             4: '6308',
                             5: '6311',
                             6: '6331',
                             7: '6316'},
                  'pins': [3, 4, 5]}}


with file(os.path.join(os.getcwd(), 'weathervane', 'tests', 'buienradar.xml'), 'rU') as f:
    data = f.read()
    wd = BuienradarParser.parse(data, 6375, **a)

print wd

bits = a['bits']
fmt = ''
for i, data in enumerate(bits):
    formatting = bits[str(i)]
    s = "hex:{0}={1},".format(formatting['length'], formatting['key'])
    fmt += s
qqq = fmt[:-1]
import bitstring

result = {}
index = 0
for key, value in bits.items():
    fmt = value
    value = wd._asdict().get(fmt['key'], 0)
    value -= float(fmt.get('min', 0))
    value /= float(fmt.get('step', 1))
    value = int(value)
    result[fmt['key']] = value
    index += 1

print 'result: ', result
print 'qqq: ', qqq

bitstring.pack(qqq, **result)