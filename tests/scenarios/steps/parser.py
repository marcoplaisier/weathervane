import datetime
from pprint import pprint

from behave import *

from weathervane.parser import BuienradarParser

use_step_matcher("re")


@given("Buienradar XML data for a single station")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.xml = """<buienradarnl>
        <weergegevens>
            <actueel_weer>
                <weerstations>
                    <weerstation id="1">
                        <stationcode>1</stationcode>
                        <stationnaam regio="Arnhem">Meetstation Arnhem</stationnaam>
                        <lat>52.04</lat>
                        <lon>5.53</lon>
                        <datum>05/14/2015 16:50:00</datum>
                        <luchtvochtigheid>47</luchtvochtigheid>
                        <temperatuurGC>15.2</temperatuurGC>
                        <windsnelheidMS>5.01</windsnelheidMS>
                        <windsnelheidBF>3</windsnelheidBF>
                        <windrichtingGR>58.7</windrichtingGR>
                        <windrichting>ONO</windrichting>
                        <luchtdruk>1011.560</luchtdruk>
                        <zichtmeters>37000</zichtmeters>
                        <windstotenMS>8.2</windstotenMS>
                        <regenMMPU>45.2</regenMMPU>
                        <icoonactueel zin="zonnig" ID="a">http://xml.buienradar.nl/icons/a.gif</icoonactueel>
                        <temperatuur10cm>18.0</temperatuur10cm>
                        <url>
                            http://www.buienradar.nl/weerstation/6275/Meetstation Arnhem
                        </url>
                        <latGraden>52.07</latGraden>
                        <lonGraden>5.88</lonGraden>
                    </weerstation>
                </weerstations>
        </weergegevens>
    </buienradarnl>"""


@when("the parser parses the data")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.parser = BuienradarParser(stations=[1, 2])
    bits = {
        '0': {'key': 'wind_direction'},
        '1': {'key': 'wind_speed'},
        '2': {'key': 'wind_speed_max'},
        '3': {'key': 'wind_speed_bft'},
        '4': {'key': 'air_pressure'},
        '5': {'key': 'temperature'},
        '6': {'key': 'apparent_temperature'},
        '7': {'key': 'humidity'},
        '8': {'key': 'station_name'},
        '9': {'key': 'latitude'},
        '10': {'key': 'longitude'},
        '11': {'key': 'date'},
        '12': {'key': 'wind_direction_code'},
        '13': {'key': 'sight_distance'},
        '14': {'key': 'rain_mm_per_hour'},
        '15': {'key': 'temperature_10_cm'},
        '16': {'key': 'barometric_trend'},
        '17': {'key': 'data_from_fallback'}
    }
    context.result = context.parser.parse(context.xml, bits=bits)


@then("usable weatherdata is returned")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assert context.result['wind_direction'] == "ONO"
    assert context.result['wind_speed'] == 5.01
    assert context.result['wind_speed_max'] == 8.2
    assert context.result['wind_speed_bft'] == 3
    assert context.result['air_pressure'] == 1011.560
    assert context.result['temperature'] == 15.2
    assert context.result['apparent_temperature'] == 15.2
    assert context.result['humidity'] == 47
    assert context.result['station_name'] == "Meetstation Arnhem"
    assert context.result['date'] == datetime.datetime(2015,5,14,16,50)
    assert context.result['wind_direction_code'] == "ONO"
    assert context.result['sight_distance'] == 37000
    assert context.result['rain_mm_per_hour'] == 45.2
    assert context.result['temperature_10_cm'] == 18.0
    assert context.result['barometric_trend'] == 4
    assert context.result['data_from_fallback'] == False
    assert context.result['latitude'] == 52.04
    assert context.result['longitude'] == 5.53


@given("Buienradar XML data for two stations where some measurements are missing from the primary station")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    context.xml = """<buienradarnl>
        <weergegevens>
            <actueel_weer>
                <weerstations>
                    <weerstation id="1">
                        <stationcode>1</stationcode>
                        <stationnaam regio="test_station_1">Meetstation 1</stationnaam>
                        <lat>45.00</lat>
                        <lon>45.00</lon>
                        <datum>05/14/2015 16:50:00</datum>
                        <luchtvochtigheid>50</luchtvochtigheid>
                        <temperatuurGC>-</temperatuurGC>
                        <windsnelheidMS>3</windsnelheidMS>
                        <windsnelheidBF>1</windsnelheidBF>
                        <windrichtingGR>90</windrichtingGR>
                        <windrichting>W</windrichting>
                        <luchtdruk>-</luchtdruk>
                        <zichtmeters>10000</zichtmeters>
                        <windstotenMS></windstotenMS>
                        <regenMMPU>-</regenMMPU>
                        <temperatuur10cm>24.0</temperatuur10cm>
                    </weerstation>
                    <weerstation id="2">
                        <stationcode>2</stationcode>
                        <stationnaam regio="test_station_2">Meetstation 2</stationnaam>
                        <lat>-45.00.04</lat>
                        <lon>-45.00</lon>
                        <datum>05/14/2015 16:50:00</datum>
                        <luchtvochtigheid>75</luchtvochtigheid>
                        <temperatuurGC>18</temperatuurGC>
                        <windsnelheidMS>5.01</windsnelheidMS>
                        <windsnelheidBF>3</windsnelheidBF>
                        <windrichtingGR>58.7</windrichtingGR>
                        <windrichting>ONO</windrichting>
                        <luchtdruk>1050.0</luchtdruk>
                        <zichtmeters>37000</zichtmeters>
                        <windstotenMS>8.2</windstotenMS>
                        <regenMMPU>-</regenMMPU>
                        <temperatuur10cm>18.0</temperatuur10cm>
                    </weerstation>
                </weerstations>
        </weergegevens>
    </buienradarnl>"""


@then("usable weatherdata is returned where the missing measurement is supplier by the fallback station")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    assert context.result['wind_direction'] == "W"
    assert context.result['wind_speed'] == 3
    assert context.result['wind_speed_max'] == 8.2
    assert context.result['wind_speed_bft'] == 1
    assert context.result['air_pressure'] == 1050
    assert context.result['temperature'] == 18
    assert context.result['humidity'] == 50
    assert context.result['station_name'] == "Meetstation 1"
    assert context.result['date'] == datetime.datetime(2015,5,14,16,50)
    assert context.result['wind_direction_code'] == "W"
    assert context.result['sight_distance'] == 10000
    assert context.result['rain_mm_per_hour'] == 0.0
    assert context.result['temperature_10_cm'] == 24.0
    assert context.result['barometric_trend'] == 4
    assert context.result['data_from_fallback'] == True
    assert context.result['latitude'] == 45
    assert context.result['longitude'] == 45
