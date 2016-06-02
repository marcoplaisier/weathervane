#!/usr/bin/python
# -*- coding: utf-8 -*-
from hypothesis import given
from hypothesis.strategies import floats

from weathervane.weather import Weather


@given(wind=floats(0), temp=floats())
def test_wind_chill(wind, temp):
    assert type(Weather.wind_chill(wind_speed=wind, temperature=temp)) == float
