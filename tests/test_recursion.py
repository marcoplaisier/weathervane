import os
import unittest
from multiprocessing import Process, Pipe

import time

from weathervane.datasources import fetch_weather_data
from weathervane.parser import WeathervaneConfigParser

class RecursionTest(unittest.TestCase):
    def test_recursion(self):
        p_end1, p_end2 = Pipe()
        cp = WeathervaneConfigParser()
        config_file = os.path.join(os.getcwd(), 'tests', 'config-test1.ini')
        cp.read(config_file)
        c = cp.parse_config()
        p = Process(target=fetch_weather_data, args=[p_end1, '6308'], kwargs=c)
        p.start()
        while not p_end2.poll():
            time.sleep(0.1)

        result = p_end2.recv()