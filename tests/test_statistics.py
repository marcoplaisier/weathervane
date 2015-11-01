from unittest import TestCase
import math
from weathervane.parser import Statistics


class TestStatistics(TestCase):
    def test_average(self):
        min = 0
        max = 1
        a = [min, max]
        expected = (min + max) / 2.0
        result = Statistics.average(a)
        self.assertEqual(expected, result)

    def test_std_dev(self):
        min = 0
        max = 1
        a = [min, max]
        expected = math.sqrt(2 * ((0.5) ** 2))
        result = Statistics.std_dev(a)
        self.assertEqual(expected, result)

    def test_trend_up(self):
        a = [0, 0, 1]
        expected = 1
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

    def test_trend_down(self):
        a = [0, 0, -1]
        expected = -1
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

    def test_trend_stable_0(self):
        a = [0, 0, 0]
        expected = 0
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

    def test_trend_stable_1(self):
        a = [4, 6, 4]
        expected = 0
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

    def test_trend_stable_2(self):
        a = [1000, 900, 987, 1029, 1009]
        expected = 0
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

    def test_trend_down_2(self):
        a = [1000, 900, 987, 1029, 900]
        print(Statistics.average(a), Statistics.std_dev(a))
        expected = -1
        result = Statistics.trend(a)
        self.assertEqual(expected, result)

