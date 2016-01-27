import time
from behave import *

from weathervane.weathervaneinterface import Display

use_step_matcher("parse")


@given("a display")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    start_time = time.localtime()
    end_time = time.mktime((
        start_time.tm_year,
        start_time.tm_mon,
        start_time.tm_mday,
        start_time.tm_hour,
        start_time.tm_min,
        start_time.tm_sec + 1,
        start_time.tm_wday,
        start_time.tm_yday,
        start_time.tm_isdst
    ))
    context.display = Display(start_time, end_time=end_time)


@given("the display is turned {status}")
def step_impl(context, status):
    """
    :type context: behave.runner.Context
    """
    context.display.status = status
    assert context.display.is_on() == status


@when("the {switch_time} time is reached")
def step_impl(context, switch_time):
    """
    :type context: behave.runner.Context
    """
    if switch_time == 'turn-off':
        time.sleep(2)

    context.display.tick()


@then("the display is turned {status}")
def step_impl(context, status):
    """
    :type context: behave.runner.Context
    """
    if status == 'on':
        assert context.display.is_on()
    else:
        assert not context.display.is_on()
