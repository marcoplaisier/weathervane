import pytest

from weathervane.weathervaneinterface import Display


class TestConvertToMinutes:
    def test_midnight(self):
        assert Display.convert_to_minutes("0:00") == 0

    def test_one_hour(self):
        assert Display.convert_to_minutes("1:00") == 60

    def test_half_past_six(self):
        assert Display.convert_to_minutes("6:30") == 390

    def test_end_of_day(self):
        assert Display.convert_to_minutes("23:59") == 1439

    def test_noon(self):
        assert Display.convert_to_minutes("12:00") == 720

    def test_with_minutes(self):
        assert Display.convert_to_minutes("14:45") == 885


class TestIsActive:
    @pytest.fixture
    def display(self):
        """Create a Display with mocked GPIO, active 6:30 - 22:00."""
        d = Display.__new__(Display)
        d.auto_disable_display = True
        d.start_at_minutes = Display.convert_to_minutes("6:30")
        d.end_at_minutes = Display.convert_to_minutes("22:00")
        return d

    def test_active_during_day(self, display):
        assert display.is_active(720) is True  # noon

    def test_active_at_start_time(self, display):
        assert display.is_active(390) is True  # 6:30

    def test_active_at_end_time(self, display):
        assert display.is_active(1320) is True  # 22:00

    def test_inactive_before_start(self, display):
        assert display.is_active(300) is False  # 5:00

    def test_inactive_after_end(self, display):
        assert display.is_active(1380) is False  # 23:00

    def test_inactive_at_midnight(self, display):
        assert display.is_active(0) is False


class TestIsActiveOvernight:
    """Schedule where start > end, e.g. turn on at 8:00, turn off at 0:30."""

    @pytest.fixture
    def display(self):
        d = Display.__new__(Display)
        d.auto_disable_display = True
        d.start_at_minutes = Display.convert_to_minutes("8:00")  # 480
        d.end_at_minutes = Display.convert_to_minutes("0:30")    # 30
        return d

    def test_active_in_evening(self, display):
        assert display.is_active(1320) is True  # 22:00

    def test_active_at_midnight(self, display):
        assert display.is_active(0) is True

    def test_active_just_before_turn_off(self, display):
        assert display.is_active(30) is True  # 0:30

    def test_active_at_start_time(self, display):
        assert display.is_active(480) is True  # 8:00

    def test_inactive_early_morning(self, display):
        assert display.is_active(120) is False  # 2:00

    def test_inactive_midday(self, display):
        assert display.is_active(420) is False  # 7:00
