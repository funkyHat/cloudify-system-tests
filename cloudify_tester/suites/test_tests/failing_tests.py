"""
This file won't be used automatically because it doesn't match pytest's
expected naming.
Run `py.test suites/test_tests/failing_tests.py` to use it.
"""
import pytest


pytest_plugins = "cloudify_tester.framework.logger"


@pytest.fixture
def has(): pass


some = pytest.fixture(lambda: None)


@pytest.fixture
def failing_fixture(has, some, args=False):
    assert args is True


def test_fail(logger):
    """Demonstrating pytest's advanced assert reporting.
    Note that it shows the evaluated value in the report"""
    value = False
    logger.info("Example log message")
    assert value is True


def test_fail_in_fixture(failing_fixture):
    """
    This test will fail even though it's empty. Assertions can be in your
    fixtures too.
    """


@pytest.mark.xfail
def test_expected_fail():
    pass
