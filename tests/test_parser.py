import unittest
import os
from parser.parser import BuienRadarParser

class ParserTestCase(unittest.TestCase):
    def setUp(self):
        file_location = os.path.join(os.getcwd(), "tests", "data.txt")
        response = open(file_location)
        self.parser = BuienRadarParser(response)

    def test_station_codes(self):
        station_codes = self.parser.get_station_codes()
        expected_codes = [u'6391', u'6275', u'6249', u'6308', u'6260', 
                          u'6235', u'6370', u'6377', u'6321', u'6350', 
                          u'6323', u'6283', u'6280', u'6315', u'6278',
                          u'6356', u'6330', u'6311', u'6279', u'6251',
                          u'6258', u'6285', u'6209', u'6225', u'6210', 
                          u'6277', u'6320', u'6270', u'6269', u'6348', 
                          u'6380', u'6273', u'6286', u'6312', u'6344', 
                          u'6343', u'6316', u'6240', u'6324', u'6267', 
                          u'6229', u'6331', u'6290', u'6313', u'6242', 
                          u'6310', u'6375', u'6319', u'6248', u'6257', 
                          u'6340', u'6239', u'6252']
        self.assertEqual(station_codes, expected_codes)

if __name__ == "__main__":
    unittest.main()
