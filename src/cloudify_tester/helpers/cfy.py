import os

import pytest
import yaml


pytest_plugins = ['cloudify_tester.framework.executor']


class CfyHelperBase(object):
    def __init__(self, workdir, executor):
        self.workdir = workdir
        self._executor = executor

    def _exec(self, command, install_plugins=False,
              retries=3, retry_delay=3, fake_run=False):
        prepared_command = ['cfy']
        command = [str(component) for component in command]
        prepared_command.extend(command)
        if install_plugins:
            prepared_command.append('--install-plugins')
        return self._executor(
            self.workdir,
            prepared_command,
            retries=retries,
            retry_delay=retry_delay,
            path_prepends=['bin'],
            fake=fake_run,
        )


class CfyHelper(CfyHelperBase):
    def __init__(self, workdir, executor):
        super(CfyHelper, self).__init__(workdir=workdir, executor=executor)
        self.local = _CfyLocalHelper(workdir=workdir, executor=executor)
        self.blueprints = _CfyBlueprintsHelper(
            workdir=workdir,
            executor=executor
        )
        self.deployments = _CfyDeploymentsHelper(
            workdir=workdir,
            executor=executor,
        )
        self.executions = _CfyExecutionsHelper(
            workdir=workdir,
            executor=executor,
        )

    def create_inputs(self, inputs_dict, inputs_name='inputs.yaml'):
        inputs_yaml = yaml.dump(inputs_dict)
        with open(os.path.join(self.workdir, inputs_name),
                  'w') as inputs_handle:
            inputs_handle.write(inputs_yaml)

    def init(self, fake_run=False):
        return self._exec(['init'], fake_run=fake_run)

    def bootstrap(self, blueprint_path, inputs_path, install_plugins=False,
                  fake_run=False):
        return self._exec(
            [
                'bootstrap',
                '--blueprint-path', blueprint_path,
                '--inputs', inputs_path,
            ],
            install_plugins=install_plugins,
            fake_run=fake_run,
        )

    def teardown(self, ignore_deployments=False, fake_run=False):
        command = ['teardown', '-f']
        if ignore_deployments:
            command.append('--ignore-deployments')
        return self._exec(command, fake_run=fake_run)


class _CfyLocalHelper(CfyHelperBase):
    def init(self, blueprint_path, inputs_path, install_plugins=False,
             fake_run=False):
        return self._exec(
            [
                'local', 'init',
                '--blueprint-path', blueprint_path,
                '--inputs', inputs_path,
            ],
            install_plugins=install_plugins,
            fake_run=fake_run,
        )

    def execute(self, workflow, fake_run=False):
        return self._exec(['local', 'execute', '--workflow', workflow],
                          fake_run=fake_run)


class _CfyBlueprintsHelper(CfyHelperBase):
    def upload(self, blueprint_path, blueprint_id, validate=False,
               fake_run=False):
        command = [
            'blueprints', 'upload',
            '--blueprint-path', blueprint_path,
            '--blueprint-id', blueprint_id,
        ]
        if validate:
            command.append('--validate')
        return self._exec(command, fake_run=fake_run)

    def delete(self, blueprint_id, fake_run=False):
        return self._exec(
            [
                'blueprints', 'delete',
                '--blueprint-id', blueprint_id,
            ],
            fake_run=fake_run,
        )


class _CfyDeploymentsHelper(CfyHelperBase):
    def create(self, blueprint_id, deployment_id, inputs_path=None,
               fake_run=False):
        command = [
            'deployments', 'create',
            '--blueprint-id', blueprint_id,
            '--deployment-id', deployment_id,
        ]
        if inputs_path is not None:
            command.extend(['--inputs', inputs_path])
        return self._exec(command, fake_run=fake_run)

    def delete(self, deployment_id, ignore_live_nodes=False, fake_run=False):
        command = [
            'deployments', 'delete',
            '--deployment-id', deployment_id,
        ]
        if ignore_live_nodes:
            command.append('--ignore-live-nodes')
        return self._exec(command, fake_run=fake_run)

    def outputs(self, deployment_id, fake_run=False):
        command = [
            'deployments', 'outputs',
            '--deployment-id', deployment_id,
            ]
        output = self._exec(command, fake_run=fake_run)
        return yaml.load('\n'.join(output['stdout'].splitlines()[1:]))


class _CfyExecutionsHelper(CfyHelperBase):
    def start(self, deployment_id, workflow, timeout=900, fake_run=False):
        command = [
            'executions', 'start',
            '--deployment-id', deployment_id,
            '--workflow', workflow,
            '--timeout', timeout,
        ]
        return self._exec(command, fake_run=fake_run)


@pytest.fixture
def cfyhelper(tmpdir, executor):
    return CfyHelper(str(tmpdir), executor)


@pytest.fixture(scope='session')
def persistentcfyhelper(tmpdir_factory, executor):
    # Because this is a session-scoped fixture we can't use the regular
    # `tmpdir` fixture as that's function-scoped.
    return CfyHelper(str(tmpdir_factory.mktemp('cfyhelper')), executor)


@pytest.yield_fixture(scope='session')
def session_manager(config, persistentgithelper, persistentcfyhelper):
    persistentgithelper.clone(
        "https://github.com/cloudify-cosmo/cloudify-manager-blueprints.git")
    persistentgithelper.checkout(
        'cloudify-manager-blueprints', config['cloudify_version'])
    inputs = {
        'instance_type': 'm3.large',
        }
    inputs.update(config['platform_options']['manager_blueprint_inputs'])
    persistentcfyhelper.create_inputs(inputs)
    persistentcfyhelper.init()
    persistentcfyhelper.bootstrap(
        os.path.join(
            persistentgithelper.workdir,
            'cloudify-manager-blueprints',
            config['platform_options']['manager_blueprint']),
        'inputs.yaml',
        install_plugins=True)

    import pdb; pdb.set_trace()

    yield persistentcfyhelper

    persistentcfyhelper.teardown()
