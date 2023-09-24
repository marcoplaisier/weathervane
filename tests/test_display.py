import time
from unittest.mock import Mock

from weathervane.weathervaneinterface import Display


def test_display_is_not_active_before_630():
    d = Display(interface=None)
    current_minute = Display.convert_to_minutes("6:29")
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
    current_minute = Display.convert_to_minutes("22:01")
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


def test_start_0700_end_2300():
    start_time = "07:00"
    end_time = "23:00"

    configuration = {'start-time': start_time, 'end-time': end_time}

    start_minute = Display.convert_to_minutes(start_time)
    end_minute = Display.convert_to_minutes(end_time)

    d = Display(interface=None, **configuration)
    print(d.end_at_minutes)
    assert end_minute == 23 * 60
    for i in range(start_minute, end_minute):
        assert d.is_active(i), f"{i} = {i // 60}:{i % 60:02}"

    assert not d.is_active(start_minute - 1)
    assert not d.is_active(end_minute + 1)


def test_start_0000_end_2300():
    start_time = "00:00"
    end_time = "23:00"

    configuration = {'start-time': start_time, 'end-time': end_time}

    start_minute = Display.convert_to_minutes(start_time)
    end_minute = Display.convert_to_minutes(end_time)

    d = Display(interface=None, **configuration)
    print(d.end_at_minutes)
    assert end_minute == 23 * 60
    for i in range(start_minute, end_minute):
        assert d.is_active(i), f"{i} = {i // 60}:{i % 60:02}"

    assert not d.is_active(Display.convert_to_minutes("23:59"))
    assert not d.is_active(end_minute + 1)


def test_start_0700_end_0100():
    start_time = "07:00"
    end_time = "01:00"

    configuration = {'start-time': start_time, 'end-time': end_time}

    start_minute = Display.convert_to_minutes(start_time)
    end_minute = Display.convert_to_minutes(end_time)

    d = Display(interface=None, **configuration)

    for i in range(start_minute, end_minute):
        assert d.is_active(i), f"{i} = {i // 60}:{i % 60:02}"

    assert not d.is_active(start_minute - 1)
    assert not d.is_active(end_minute + 1)
