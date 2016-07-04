"""
One interesting thing to note is that we're using the `tmpdir` fixture in a few
of the step implementations here, and it always returns the same path. That's
because fixtures are scoped by test by default, so the first time we use tmpdir
it's cached and then reused.
"""
import os
import urllib2
from ast import literal_eval
from time import sleep

import py
import pytest
from pytest_bdd import scenarios, given, when, then
from pytest_bdd.parsers import parse


# The scenarios function tells pytest-bdd how to find feature files. It's alos
# possible to describe features explicitly as test cases using the @scenario
# decorator, but I didn't need to customise so this is fine.
scenarios('features')


@given("I run a step which fails")
def failing_step():
    pytest.fail("Oh no!")


@given(parse("I have a local blueprint at {path}"))
def blueprint_path(path):
    """
    Steps are actually pytest fixtures, this means their return values are
    cached and can be used by subsequent steps using the normal pytest fixture
    syntax.
    """
    return os.path.join(os.path.dirname(__file__), path)


@given(parse("I create inputs file '{filename}' with inputs"
             '\n"""\n{text}\n"""'))
def inputs_file(filename, text, tmpdir):
    file_path = os.path.join(str(tmpdir), filename)
    with open(file_path, 'w') as f:
        f.write(text)
    return file_path


@when("I init a local env using the blueprint")
def init_env(blueprint_path, inputs_file, cfyhelper):
    """
    Note here `blueprint_path` (from the first step) is pulled in as a
    fixture.
    Also note that the `cfyhelper` fixture which we use in some of the non-bdd
    test cases is used here in exactly the same way (it's loaded by
    conftest.py).
    """
    cfyhelper.local.init(blueprint_path, inputs_file)


@when(parse("I execute the local {name:w} workflow"))
def execute_workflow(name, cfyhelper):
    cfyhelper.local.execute(workflow=name)


@then(parse("I see the file {file} exists"))
def check_file_exists(cfyhelper, file):
    with py.path.local(cfyhelper.workdir).as_cwd():
        assert os.path.isfile(file)
    return file


@then(parse("The file {file} contains the text '{text}'"))
def check_contents(file, text, cfyhelper):
    with py.path.local(cfyhelper.workdir).as_cwd(), open(file) as f:
        assert text in f.read()


@given(parse("I have a manager"))
def deployed_manager(session_manager):
    return session_manager


@given("I upload the nodecellar blueprint")
def upload_blueprint(
        request, session_manager, clone_git_repo, config):
    session_manager.blueprints.upload(
        os.path.join(
            clone_git_repo,
            config['platform_options']['nodecellar_blueprint']),
        'nodecellar')

    def remove():
        session_manager.blueprints.delete('nodecellar')
    request.addfinalizer(remove)


@given(parse("I create a '{blueprint}' deployment with the ID '{id}'"))
def deployment(
        request, config, deployed_manager, clone_git_repo,
        blueprint, id, inputs_file,
        ):
    deployed_manager.deployments.create('nodecellar', id, inputs_file)

    def remove():
        deployed_manager.executions.start(id, 'uninstall')
        deployed_manager.deployments.delete(id)
    request.addfinalizer(remove)

    # Here I'm creating a `deployment` dictionary. This will be passed to any
    # subesequent step which asks for this fixture. Using a dictionary (or
    # another mutable type) allows me to store side-effects for later use, in
    # the same way that the `context` step argument does in behave. However
    # this allows more fine-grained context for different steps, if desired.
    return {'manager': deployed_manager, 'id': id}


@given(parse("I run the '{workflow}' workflow"))
def run_workflow(deployed_manager, deployment, workflow):
    deployed_manager.executions.start(deployment['id'], workflow)


@when("I look up the monitoring data for the deployment")
def get_monitoring_data(logger, deployment):
    sleep(3)
    logger.warn("You caught me. I didn't really look at the monitoring data!")


@pytest.fixture
def deployment_host_port(deployed_manager, deployment):
    outputs = deployed_manager.deployments.outputs(deployment['id'])

    values = outputs[0]['endpoint']['Value']
    # really not sure why the strings in the outputs are weird like this
    return literal_eval(values["u'ip_address'"]), values["u'port'"]


@then(parse("if I visit the deployment's front page I see '{text}'"))
def i_visit_the_nodecellar_url(deployment_host_port, text):
    """I visit the nodecellar URL."""
    page = urllib2.urlopen('http://{}:{}/'.format(*deployment_host_port))

    assert text in page.read()


@then('monitoring data is present')
def monitoring_data_is_present(logger, deployment):
    """monitoring data is present."""
    logger.warn("whoops")
