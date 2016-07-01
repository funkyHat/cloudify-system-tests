

pytest_plugins = (
    'cloudify_tester.framework.config',
    'cloudify_tester.framework.cfy',
    'cloudify_tester.framework.git',
    )


def pytest_bdd_before_step_call(request, feature, scenario, step, *args):
    print('{} {}'.format(step.keyword, step.name))
