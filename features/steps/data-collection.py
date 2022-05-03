from behave import use_step_matcher, given, then, when, step

use_step_matcher("re")


@then("we have the data")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@given("the system is online")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@when("we collect data from buienradar")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@step("buienradar is not reachable")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass


@then("we have dummy data")
def step_impl(context):
    """
    :type context behave.runner.Context
    """
    pass
