#!/usr/bin/python
# -*- coding: utf-8 -*-
import os

from weathervane.parser import WeathervaneConfigParser

config_file_name = "config-test1.ini"


def test_parse_config():
    config_file = os.path.join(os.getcwd(), "tests", config_file_name)
    cp = WeathervaneConfigParser()
    cp.read(config_file)
    expected_keys = [
        "channel",
        "frequency",
        "library",
        "data_collection_interval",
        "data_display_interval",
        "source",
        "stations",
        "bits",
        "test",
        "barometric_trend",
        "display",
    ]
    observed = cp.parse_config()
    assert set(observed.keys()) == set(expected_keys)
    assert len(observed["bits"]) == 16


def test_parse_station_numbers():
    config_file = os.path.join(os.getcwd(), "tests", config_file_name)
    cp = WeathervaneConfigParser()
    cp.read(config_file)
    stations = cp.parse_station_numbers()
    assert stations == [6323, 6283]


def test_rain_config():
    "Tests if rain configuration is correctly picked up. E.g. bit_13=rainFallLastHour,10,0,99.9,0.1"
    config_file = os.path.join(os.getcwd(), "tests", config_file_name)
    cp = WeathervaneConfigParser()
    cp.read(config_file)
    observed = cp.parse_config()
    rain_config = observed["bits"][13]
    assert rain_config == {
        "key": "rainFallLastHour",
        "length": "10",
        "min": "0",
        "max": "99.9",
        "step": "0.1",
    }
