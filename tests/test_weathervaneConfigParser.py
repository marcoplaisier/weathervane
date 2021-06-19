#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from unittest import TestCase

from weathervane.parser import WeathervaneConfigParser


class TestWeathervaneConfigParser(TestCase):
    def test_parse_config(self):
        config_file = os.path.join(os.getcwd(), 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        observed = cp.parse_config()
        expected_keys = ['extended-error-mode', 'channel', 'frequency', 'library', 'interval', 'source',
                         'stations', 'bits', 'sleep-time', 'test', 'barometric_trend', 'display']
        self.assertEqual(set(observed.keys()), set(expected_keys))
        self.assertEqual(16, len(observed['bits']))

    def test_parse_station_numbers(self):
        config_file = os.path.join(os.getcwd(), 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        stations = cp.parse_station_numbers()
        assert stations == [6320, 6308]

    def test_rain_config(self):
        'Tests if rain configuration is correctly picked up. E.g. bit_13=rainFallLastHour,10,0,99.9,0.1'
        config_file = os.path.join(os.getcwd(), 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        observed = cp.parse_config()
        rain_config = observed['bits'][13]
        assert rain_config == {
            'key': 'rainFallLastHour',
            'length': '10',
            'min': '0',
            'max': '99.9',
            'step': '0.1'
        }
