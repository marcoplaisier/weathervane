from behave import given, step, then, use_step_matcher, when

use_step_matcher("parse")


@given("a display")
def step_impl(context):
    """
    :type context: behave.runner.Context
    """
    pass


@given("the display is turned {status}")
def step_impl(context, status):
    """
    :type context: behave.runner.Context
    """

    pass


@when("the {switch_time} time is reached")
def step_impl(context, switch_time):
    """
    :type context: behave.runner.Context
    """

    pass


@then("the display is turned {status}")
def step_impl(context, status):
    """
    :type context: behave.runner.Context
    """

    pass
