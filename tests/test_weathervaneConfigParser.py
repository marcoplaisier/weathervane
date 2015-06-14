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
                         'fallback-station', 'stations', 'bits', 'sleep-time']
        self.assertEqual(set(observed.keys()), set(expected_keys))
        expected_bits = {str(x): x for x in range(12)}
        self.assertEqual(set(expected_bits.keys()), set(observed['bits'].keys()))

    def test_parse_station_numbers(self):
        config_file = os.path.join(os.getcwd(), 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        cp.parse_station_numbers()
