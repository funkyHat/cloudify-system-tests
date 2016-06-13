"""
This file won't be used automatically because it doesn't match pytest's
expected naming.
Run `py.test suites/test_tests/failing_tests.py` to use it.
"""


def test_fail():
    """Demonstrating pytest's advanced assert reporting.
    Note that it shows the evaluated value in the report"""
    value = False
    assert value is True
