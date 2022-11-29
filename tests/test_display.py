import time
from unittest.mock import Mock

from weathervane.weathervaneinterface import Display


def test_display_is_not_active_before_630():
    d = Display(interface=None)
    current_minute = Display.convert_to_minutes("6:30")
    result = d.is_active(current_minute=current_minute)
    expected = False
    assert result == expected


def test_display_is_active_at_630():
    d = Display(interface=None)
    current_minute = Display.convert_to_minutes("6:31")
    result = d.is_active(current_minute=current_minute)
    expected = True
    assert result == expected


def test_display_is_active_before_2200():
    d = Display(interface=None)
    current_minute = Display.convert_to_minutes("21:59")
    result = d.is_active(current_minute=current_minute)
    expected = True
    assert result == expected


def test_display_is_not_active_at_2201():
    d = Display(interface=None)
    current_minute = Display.convert_to_minutes("22:00")
    result = d.is_active(current_minute=current_minute)
    expected = False
    assert result == expected


def test_tick():
    interface = Mock()
    interface.gpio = Mock()
    interface.gpio.write_pin = Mock()
    d = Display(interface=interface)
    d.auto_disable_display = True
    active = d.is_active(Display.convert_to_minutes(time.strftime("%H:%M")))
    d.tick()
    if active:
        assert interface.gpio.write_pin.assert_called_once_with(d.pin, 1) is None
    else:
        assert interface.gpio.write_pin.assert_called_once_with(d.pin, 0) is None


def test_no_tick():
    interface = Mock()
    interface.gpio = Mock()
    interface.gpio.write_pin = Mock()
    d = Display(interface=interface)
    d.auto_disable_display = False
    d.tick()
    assert interface.gpio.write_pin.assert_not_called() is None


def test_convert_630_to_minutes():
    d = Display(interface=None)
    minutes = d.convert_to_minutes("6:30")
    assert 6 * 60 + 30 == minutes


def test_convert_2200_to_minutes():
    d = Display(interface=None)
    minutes = d.convert_to_minutes("22:00")
    assert 22 * 60 == minutes
