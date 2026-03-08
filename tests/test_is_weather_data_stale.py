from datetime import datetime, timedelta

from weathervane.parser import is_weather_data_stale


class TestIsWeatherDataStale:
    def test_fresh_data_is_not_stale(self):
        now = datetime(2025, 6, 15, 12, 0, 0)
        timestamp = (now - timedelta(minutes=30)).isoformat()
        assert is_weather_data_stale(timestamp, now) is False

    def test_data_exactly_at_limit_is_not_stale(self):
        now = datetime(2025, 6, 15, 12, 0, 0)
        timestamp = (now - timedelta(hours=2)).isoformat()
        assert is_weather_data_stale(timestamp, now) is False

    def test_data_over_two_hours_is_stale(self):
        now = datetime(2025, 6, 15, 12, 0, 0)
        timestamp = (now - timedelta(hours=2, seconds=1)).isoformat()
        assert is_weather_data_stale(timestamp, now) is True

    def test_very_old_data_is_stale(self):
        now = datetime(2025, 6, 15, 12, 0, 0)
        timestamp = (now - timedelta(days=1)).isoformat()
        assert is_weather_data_stale(timestamp, now) is True

    def test_recent_data_is_not_stale(self):
        now = datetime(2025, 6, 15, 12, 0, 0)
        timestamp = (now - timedelta(seconds=10)).isoformat()
        assert is_weather_data_stale(timestamp, now) is False
