class Weather(object):
    """source: http://pywws.readthedocs.io/en/latest/_modules/pywws/conversions.html"""

    @staticmethod
    def apparent_temperature(windspeed=None, temperature=None, humidity=None):
        if windspeed is None and humidity is None:
            return temperature
        if temperature < 10:
            return Weather.wind_chill(windspeed, temperature)
        else:
            return Weather.heatindex(temperature, humidity)

    @staticmethod
    def heatindex(temp, humidity):
        """Calculate Heat Index as per USA National Weather Service Standards

        See http://en.wikipedia.org/wiki/Heat_index, formula 1. The
        formula is not valid for T < 26.7C, Dew Point < 12C, or RH < 40%
        """
        if temp is None or humidity is None:
            return None
        if temp < 26.7 or humidity < 40:
            return temp
        temp_in_fahrenheit = Weather.temp_f(temp)
        R = humidity
        c_1 = -42.379
        c_2 = 2.04901523
        c_3 = 10.14333127
        c_4 = -0.22475541
        c_5 = -0.00683783
        c_6 = -0.05481717
        c_7 = 0.00122874
        c_8 = 0.00085282
        c_9 = -0.00000199
        h_index = c_1 + (c_2 * temp_in_fahrenheit) + (c_3 * R) + (c_4 * temp_in_fahrenheit * R) + \
                  (c_5 * (temp_in_fahrenheit ** 2)) + (c_6 * (R ** 2)) + (c_7 * (temp_in_fahrenheit ** 2) * R) + \
                  (c_8 * temp_in_fahrenheit * (R ** 2)) + (c_9 * (temp_in_fahrenheit ** 2) * (R ** 2))
        return round(Weather.temp_c(h_index), 1)

    @staticmethod
    def wind_chill(wind_speed, temperature):
        if wind_speed is None or temperature is None:
            return None
        if wind_speed < 0:
            raise ValueError("Wind speed must be a positive number")
        if wind_speed < 1.3:
            return temperature
        wind_chill = 13.12 + 0.6215 * temperature - 13.96 * wind_speed ** 0.16 + 0.4867 * temperature * wind_speed ** 0.16
        return round(wind_chill, 1)

    @staticmethod
    def temp_f(c):
        """Convert temperature from Celsius to Fahrenheit"""
        if c is None:
            return None
        return (c * 9.0 / 5.0) + 32.0

    @staticmethod
    def temp_c(f):
        """Convert temperature from Fahrenheit to Celsius"""
        if f is None:
            return None
        return (f - 32) * 5.0 / 9.0
