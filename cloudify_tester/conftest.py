"""
This demonstrates how to create pytest "fixtures".

`conftest.py` is a special file which pytest will always load when setting up a
test run. Any fixtures defined or declared as imports will then be available to
the tests.

tests can use fixtures by declaring an argument with the name of the fixture
(see `cloudify_tester/suites/local/test_tests.py` for an example using the
`get_all_the_tests` fixture below).
"""
import pytest
import _pytest


# pytest_plugins accepts a plugin or sequence of plugins that will be loaded
# while building the test environment. Note that the `config` fixture from
# `framework/config.py` is available and used by the `manager` fixture below as
# well as directly in some of the tests.
pytest_plugins = (
    'cloudify_tester.framework.config',
    'cloudify_tester.framework.cfy',
    )


@pytest.fixture(scope="session")
def get_all_the_tests(request):
    """shamelessly stolen from the pytest examples.
    https://pytest.org/latest/example/special.html"""
    seen = set()
    session = request.node
    for item in session.items:
        cls = item.getparent((pytest.Class, _pytest.python.Function))
        if cls not in seen:
            seen.add(cls)
    return seen


class FakeManager(object):
    fin_called = False

    def fin(self):
        self.fin_called = True


# Create one FakeManager so we can check if fin() was called by the first test
manager_obj = FakeManager()


@pytest.fixture
def manager(request, config):
    """Set up an instance so we can use a manager in tests which use this
    fixture.

    Notice that this fixture is using the config fixture.
    """
    request.addfinalizer(manager_obj.fin)
    return manager_obj
