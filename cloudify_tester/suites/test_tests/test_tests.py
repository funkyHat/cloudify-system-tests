import pytest


def test_the_tests(get_all_the_tests):
    """Check that all the tests are having a nice time"""
    for test in get_all_the_tests:
        assert 'test' in test.name


def test_the_config(config):
    """Testing the config fixture"""
    assert config['real'] is True

    with pytest.raises(KeyError):
        config['non existent config key']
