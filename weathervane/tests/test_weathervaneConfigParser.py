#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from unittest import TestCase
from weathervane.parser import WeathervaneConfigParser


class TestWeathervaneConfigParser(TestCase):
    def test_parse_config(self):
        config_file = os.path.join(os.getcwd(), 'weathervane', 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        observed = cp.parse_config()
        expected_keys = ['extended-error-mode', 'channel', 'frequency', 'library', 'interval', 'source',
                         'fallback-station', 'stations', 'bits', 'ready_pin']
        assert set(observed.keys()) == set(expected_keys)

    def test_parse_station_numbers(self):
        config_file = os.path.join(os.getcwd(), 'weathervane', 'tests', 'config-test1.ini')
        cp = WeathervaneConfigParser()
        cp.read(config_file)
        cp.parse_station_numbers()
