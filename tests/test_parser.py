import unittest
import os
from weathervane.parser.parser import BuienradarParser
from datetime import datetime

class ParserTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_station_name(self):
        testdata_excerpt = '''<weerstation id="6323">
                                  <stationnaam regio="Goes">Meetstation Goes</stationnaam>
                              </weerstation>'''
        parser = BuienradarParser(testdata_excerpt)
        expected = 'Meetstation Goes'
        result = parser.get_station_name_by_id(6323)
        self.assertEqual(expected, result, "Expected station name %s does not match %s" % (expected, result))

    def test_get_date(self):
        testdata_excerpt = '''<weerstation id="6323">
                                  <datum>11/06/2012 21:40:00</datum>
                              </weerstation>'''
        parser = BuienradarParser(testdata_excerpt)
        expected = datetime(2012, 6, 11, 21, 40, 00)
        result = parser.get_date(6323)
        self.assertEqual(result, expected, 'Expected date %s does not match result %s' % (expected, result))

    def test_get_wind_direction(self):
        test_data_excerpt = '''<weerstation id="6323"><stationcode>6323</stationcode>
                                   <stationnaam regio="Goes">Meetstation Goes</stationnaam>
                                   <windsnelheidMS>9.01</windsnelheidMS>
                               </weerstation>'''
        parser = BuienradarParser(test_data_excerpt)
        expected = 9.01
        result = parser.get_wind_speed(6323)
        self.assertEqual(result, expected, 'Expected windspeed %s does not match result %s' % (expected, result))

if __name__ == "__main__":
    unittest.main()
