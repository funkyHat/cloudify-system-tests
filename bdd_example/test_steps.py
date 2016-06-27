"""
One interesting thing to note is that we're using the `tmpdir` fixture in a few
of the step implementations here, and it always returns the same path. That's
because fixtures are scoped by test by default, so the first time we use tmpdir
it's cached and then reused.
"""
import os

from pytest_bdd import scenarios, given, when, then
from pytest_bdd.parsers import parse


# The scenarios function tells pytest-bdd how to find feature files. It's alos
# possible to describe features explicitly as test cases using the @scenario
# decorator, but I didn't need to customise so this is fine.
scenarios('features')


@given(parse("I have a local blueprint at {path}"))
def blueprint_path(path):
    """
    Steps are actually pytest fixtures, this means their return values are
    cached and can be used by subsequent steps using the normal pytest fixture
    syntax.
    """
    return os.path.join(os.path.dirname(__file__), path)


@given(parse('I create inputs file {filename} with inputs\n"""\n{text}\n"""'))
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
def check_file_exists(tmpdir, file):
    with tmpdir.as_cwd():
        assert os.path.isfile(file)
    return file


@then(parse("The file {file} contains the text '{text}'"))
def check_contents(file, text, tmpdir):
    with tmpdir.as_cwd(), open(file) as f:
        assert text in f.read()
