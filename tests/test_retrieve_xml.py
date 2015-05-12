#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from unittest import TestCase
from multiprocessing import Pipe, Process
import time
from urllib2 import URLError

from mock import patch, Mock, call

from weathervane.datasources import fetch_weather_data, DataSourceError
from weathervane import datasources
from tests.test_config import config


class TestRetrieveXML(TestCase):
    def test_retrieve_xml(self):
        url = 'file://' + os.path.join(os.getcwd(), 'tests', 'buienradar.xml')
        data = datasources.retrieve_xml(url)
        with file(os.path.join(os.getcwd(), 'tests', 'buienradar.xml')) as f:
            expected = f.read()

        assert data == expected


class TestFetchWeatherData(TestCase):
    @patch('weathervane.datasources.retrieve_xml')
    def test_fetch_weather_data(self, retrieve_function):

        p1, p2 = Pipe()
        station_id = 6330
        args = [p1, station_id]
        with patch('weathervane.datasources.BuienradarParser.parse', return_value='success') as parser:
            p = Process(target=fetch_weather_data, args=args, kwargs=config)
            p.start()

        while True:
            if p2.poll(0):
                observed = p2.recv()
                break
            else:
                time.sleep(0.1)

        expected = 'success'
        print expected
        print observed
        pass
