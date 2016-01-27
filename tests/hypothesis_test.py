#!/usr/bin/python
# -*- coding: utf-8 -*-
from hypothesis import given, assume
from hypothesis.strategies import floats, lists
import math
from weathervane.parser import BuienradarParser, Statistics

@given(wind=floats(0), temp=floats())
def test_wind_chill(wind, temp):
    assert type(BuienradarParser.calculate_wind_chill(wind_speed=wind, temperature=temp)) == float

@given(lists(floats()))
def test_average(s):
    assume(s != [])
    assume(all(not math.isnan(x) for x in s))
    assume(all(not x == float('inf') for x in s))
    assume(all(not x == float('-inf') for x in s))
    avg = Statistics.average(s)
    assert type(avg) in [float, int]
    assert avg <= max(s) or avg == float('inf') or avg == float('-inf')
    assert avg >= min(s) or avg == float('inf') or avg == float('-inf')

@given(lists(floats(-1.0e-100, 1e100)))
def test_stdev(s):
    assume(s != [])
    assume(all(not x == float('inf') for x in s))
    assume(all(not x == float('-inf') for x in s))
    stdev = Statistics.std_dev(s)
    print(type(stdev))
    assert type(stdev) in [int, float]

@given(lists(floats(-1.0e-100, 1e100)))
def test_trend(s):
    assume(s != [])
    assume(all(not x == float('inf') for x in s))
    assume(all(not x == float('-inf') for x in s))
    trend = Statistics.trend(s)
    assert trend in [-1, 0, 1]