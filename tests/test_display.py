from unittest import TestCase
from unittest.mock import Mock

import time

from weathervane.weathervaneinterface import Display


def test_display_is_not_active_before_630():
    display = Display(interface=None)
    current_minute = Display.convert_to_minutes('6:30')
    result = display.is_active(current_minute=current_minute)
    expected = False
    assert result == expected


def test_display_is_active_at_630():
    display = Display(interface=None)
    current_minute = Display.convert_to_minutes('6:31')
    result = display.is_active(current_minute=current_minute)
    expected = True
    assert result == expected


def test_display_is_active_before_2200():
    display = Display(interface=None)
    current_minute = Display.convert_to_minutes('21:59')
    result = display.is_active(current_minute=current_minute)
    expected = True
    assert result == expected


def test_display_is_not_active_at_2201():
    display = Display(interface=None)
    current_minute = Display.convert_to_minutes('22:00')
    result = display.is_active(current_minute=current_minute)
    expected = False
    assert result == expected


def test_tick():
    interface = Mock()
    interface.gpio = Mock()
    interface.gpio.write_pin = Mock()
    display = Display(interface=interface)
    display.auto_disable_display = True
    active = display.is_active(Display.convert_to_minutes(time.strftime("%H:%M")))
    display.tick()
    if active:
        assert interface.gpio.write_pin.assert_called_once_with(display.pin, 1) is None
    else:
        assert interface.gpio.write_pin.assert_called_once_with(display.pin, 0) is None


def test_no_tick():
    interface = Mock()
    interface.gpio = Mock()
    interface.gpio.write_pin = Mock()
    display = Display(interface=interface)
    display.auto_disable_display = False
    display.tick()
    assert interface.gpio.write_pin.assert_not_called() is None


def test_convert_630_to_minutes():
    display = Display(interface=None)
    minutes = display.convert_to_minutes("6:30")
    assert 6 * 60 + 30 == minutes


def test_convert_2200_to_minutes():
    display = Display(interface=None)
    minutes = display.convert_to_minutes("22:00")
    assert 22 * 60 == minutes
