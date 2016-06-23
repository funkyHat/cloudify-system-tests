

def test_importing_fixtures(config):
    assert 'framework.config.Config' in str(type(config))
    assert config['real'] is True
