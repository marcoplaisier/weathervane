from main import WeatherVane


class TestInterpolate:
    def test_returns_new_data_on_error(self):
        old = {"temperature": 10.0, "windspeed": 5.0, "error": False}
        new = {"temperature": 20.0, "windspeed": 8.0, "error": True}
        result = WeatherVane.interpolate(old, new, 0.5)
        assert result is new

    def test_returns_new_data_when_no_old_data(self):
        new = {"temperature": 20.0, "error": False}
        result = WeatherVane.interpolate(None, new, 0.5)
        assert result is new

    def test_interpolates_numeric_values(self):
        old = {"temperature": 10.0, "windspeed": 4.0, "error": False}
        new = {"temperature": 20.0, "windspeed": 8.0, "error": False}
        result = WeatherVane.interpolate(old, new, 0.5)
        assert result["temperature"] == 15.0
        assert result["windspeed"] == 6.0

    def test_percentage_zero_returns_old_values(self):
        old = {"temperature": 10.0, "error": False}
        new = {"temperature": 20.0, "error": False}
        result = WeatherVane.interpolate(old, new, 0.0)
        assert result["temperature"] == 10.0

    def test_percentage_one_returns_new_values(self):
        old = {"temperature": 10.0, "error": False}
        new = {"temperature": 20.0, "error": False}
        result = WeatherVane.interpolate(old, new, 1.0)
        assert result["temperature"] == 20.0

    def test_percentage_clamped_to_one(self):
        old = {"temperature": 10.0, "error": False}
        new = {"temperature": 20.0, "error": False}
        result = WeatherVane.interpolate(old, new, 1.5)
        assert result["temperature"] == 20.0

    def test_non_interpolatable_variables_use_new_value(self):
        old = {"winddirection": "N", "rain": 0, "barometric_trend": 4, "error": False}
        new = {"winddirection": "ZW", "rain": 1, "barometric_trend": 2, "error": False}
        result = WeatherVane.interpolate(old, new, 0.5)
        assert result["winddirection"] == "ZW"
        assert result["rain"] == 1
        assert result["barometric_trend"] == 2

    def test_missing_key_in_new_uses_old_value(self):
        old = {"temperature": 10.0, "humidity": 80, "error": False}
        new = {"temperature": 20.0, "error": False}
        result = WeatherVane.interpolate(old, new, 0.5)
        assert result["humidity"] == 80

    def test_non_numeric_values_use_new_value(self):
        old = {"stationname": "De Bilt", "error": False}
        new = {"stationname": "Schiphol", "error": False}
        result = WeatherVane.interpolate(old, new, 0.5)
        assert result["stationname"] == "Schiphol"
