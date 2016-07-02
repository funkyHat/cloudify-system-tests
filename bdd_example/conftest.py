

pytest_plugins = (
    'cloudify_tester.framework.config',
    'cloudify_tester.framework.cfy',
    'cloudify_tester.framework.git',
    )


# The following parts should be (I am likely to just do this at some point :)
# pulled out into their own package most likely.
# We can't be the only ones who want our pytest-bdd logging to actually report
# on the steps!


def pytest_bdd_before_scenario(request, feature, scenario):
    """
    This and the next are hook implementations which will be called at the
    relevant moments during pytest-bdd feature runs
    """
    print('\nFeature: {}'.format(feature.name))
    print('  Scenario: {}'.format(scenario.name))


def pytest_bdd_before_step_call(request, feature, scenario, step, *args):
    step_first_line = step.name.splitlines()[0]
    print('{}{} {}'.format(
        ' '*step.indent, step.keyword, step_first_line))
    if step.lines:
        print('\n'.join(step.lines))
