import os

import yaml

from cloudify_cli.commands import local


def test_init_simple_blueprint(tmpdir):
    """
    Using pytest built in tmpdir fixture
    """
    with tmpdir.as_cwd():
        local.init(
            blueprint_path=os.path.join(
                os.path.dirname(__file__), 'simple_blueprint/blueprint.yaml'),
            inputs=yaml.dump({
                'target_path': './a folder/',
                'target_file_name': 'file',
                }),
            install_plugins=False,
            )
        local.execute(
            workflow_id='install',
            parameters=None,
            allow_custom_parameters=False,
            task_retries=0,
            task_retry_interval=1,
            task_thread_pool_size=1)

        with open('./a folder/file') as f:
            assert 'This file contains some text. Wow!\n' == f.read()
