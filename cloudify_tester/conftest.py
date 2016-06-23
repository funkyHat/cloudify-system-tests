
import pytest
import _pytest


pytest_plugins = 'cloudify_tester.framework.config'


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
