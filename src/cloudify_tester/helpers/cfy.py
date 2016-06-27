import os
from subprocess import check_output

import pytest
import yaml


class CfyHelperBase(object):
    def __init__(self, workdir):
        self.workdir = workdir

    def _exec(self, command, install_plugins=False):
        prepared_command = ['cfy']
        prepared_command.extend(command)
        if install_plugins:
            prepared_command.append('--install-plugins')
        # TODO: Logging
        print(' '.join(prepared_command))
        check_output(prepared_command, cwd=self.workdir)


class CfyHelper(CfyHelperBase):
    def __init__(self, workdir):
        super(CfyHelper, self).__init__(workdir=workdir)
        self.local = _CfyLocalHelper(workdir=workdir)
        self.blueprints = _CfyBlueprintsHelper(workdir=workdir)
        self.deployments = _CfyDeploymentsHelper(workdir=workdir)
        self.executions = _CfyExecutionsHelper(workdir=workdir)

    def create_inputs(self, inputs_dict, inputs_name='inputs.yaml'):
        inputs_yaml = yaml.dump(inputs_dict)
        with open(os.path.join(self.workdir, inputs_name),
                  'w') as inputs_handle:
            inputs_handle.write(inputs_yaml)

    def init(self):
        return self._exec(['init'])

    def bootstrap(self, blueprint_path, inputs_path, install_plugins=False):
        return self._exec(
            [
                'bootstrap',
                '--blueprint-path', blueprint_path,
                '--inputs', inputs_path,
            ],
            install_plugins=install_plugins,
        )

    def teardown(self, ignore_deployments=False):
        command = ['teardown', '-f']
        if ignore_deployments:
            command.append('--ignore-deployments')
        return self._exec(command)


class _CfyLocalHelper(CfyHelperBase):
    def init(self, blueprint_path, inputs_path, install_plugins=False):
        return self._exec(
            [
                'local', 'init',
                '--blueprint-path', blueprint_path,
                '--inputs', inputs_path,
            ],
            install_plugins=install_plugins,
        )

    def execute(self, workflow):
        return self._exec(['local', 'execute', '--workflow', workflow])


class _CfyBlueprintsHelper(CfyHelperBase):
    def upload(self, blueprint_path, blueprint_id, validate=False):
        command = [
            'blueprints', 'upload',
            '--blueprint-path', blueprint_path,
            '--blueprint-id', blueprint_id,
        ]
        if validate:
            command.append('--validate')
        return self._exec(command)

    def delete(self, blueprint_id):
        return self._exec([
            'blueprints', 'delete',
            '--blueprint-id', blueprint_id,
        ])


class _CfyDeploymentsHelper(CfyHelperBase):
    def create(self, blueprint_id, deployment_id, inputs_path=None):
        command = [
            'deployments', 'create',
            '--blueprint-id', blueprint_id,
            '--deployment-id', deployment_id,
        ]
        if inputs_path is not None:
            command.extend(['--inputs', inputs_path])
        return self._exec(command)

    def delete(self, deployment_id, ignore_live_nodes=False):
        command = [
            'deployments', 'delete',
            '--deployment-id', deployment_id,
        ]
        if ignore_live_nodes:
            command.append('--ignore-live-nodes')
        return self._exec(command)


class _CfyExecutionsHelper(CfyHelperBase):
    def start(self, deployment_id, workflow, timeout=900):
        command = [
            'executions', 'start',
            '--deployment-id', deployment_id,
            '--workflow', workflow,
            '--timeout', timeout,
        ]
        self._exec(command)


@pytest.fixture
def cfyhelper(tmpdir):
    return CfyHelper(str(tmpdir))


@pytest.fixture(scope='session')
def persistentcfyhelper(tmpdir_factory):
    # Because this is a session-scoped fixture we can't use the regular
    # `tmpdir` fixture as that's function-scoped.
    return CfyHelper(str(tmpdir_factory.mktemp('cfyhelper')))


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

    yield persistentcfyhelper

    persistentcfyhelper.teardown()
