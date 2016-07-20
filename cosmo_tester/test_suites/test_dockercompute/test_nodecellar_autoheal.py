########
# Copyright (c) 2016 GigaSpaces Technologies Ltd. All rights reserved
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
#    * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    * See the License for the specific language governing permissions and
#    * limitations under the License.

import time
import shutil

from cosmo_tester.framework.git_helper import clone
from cosmo_tester.framework.util import YamlPatcher
from cosmo_tester.test_suites.test_dockercompute import DockerComputeTestCase
from cosmo_tester.test_suites.test_blueprints.nodecellar_test import (
    NodecellarAppTest)


class DockerComputeNodeCellarAutoHealTest(DockerComputeTestCase,
                                          NodecellarAppTest):

    def test_dockercompute_nodecellar_autoheal(self):
        blueprint_file = 'dockercompute-blueprint.yaml'
        self.repo_dir = clone(self.repo_url, self.workdir, self.repo_branch)
        self.blueprint_yaml = self.repo_dir / blueprint_file
        shutil.copy(self.blueprint_resource_path(
            'nodecellar/{0}'.format(blueprint_file)),
            self.blueprint_yaml)
        shutil.copy(self.blueprint_resource_path(
            'nodecellar/types/dockercompute-types.yaml'),
            self.repo_dir / 'types' / 'dockercompute-types.yaml')
        self.add_plugin_yaml_to_blueprint()
        with YamlPatcher(self.blueprint_yaml) as patch:
            patch.merge_obj('groups', self.autoheal_group_yaml)
        self.install(fetch_state=False)
        self.deployment_id = self.test_id
        self.assert_monitoring_data_exists()
        connect_timeout = 1
        ip = self.ip('nodejs_host')
        url = 'http://{0}:{1}/wines'.format(ip, self.nodecellar_port)
        response = self.request(url, json=True,
                                connect_timeout=connect_timeout)
        self.assertEqual(list, type(response))
        self.assertGreater(len(response), 1)
        self.kill_nodejs_vm()
        self.assertRaises(RuntimeError, self.request, url,
                          connect_timeout=connect_timeout)
        self.wait_for_autoheal()
        wines_response = self.request(url, json=True,
                                      connect_timeout=connect_timeout)
        self.assertEqual(list, type(wines_response))
        self.assertGreater(len(wines_response), 1)
        self.execute_uninstall(deployment_id=self.test_id,
                               delete_deployment_and_blueprint=True)
        self.assertRaises(RuntimeError, self.request, url,
                          connect_timeout=connect_timeout)

    def kill_nodejs_vm(self):
        self.kill_container(node_id='nodejs_host')

    def wait_for_autoheal(self, timeout=1200):
        end = time.time() + timeout
        autoheal_execution = None

        while time.time() < end:
            autoheal_execution = self.get_autoheal_execution()
            if autoheal_execution is not None:
                break
            time.sleep(10)

        self.assertIsNotNone(autoheal_execution, msg="Timed out waiting "
                                                     "for auto-heal workflow")
        self.wait_for_execution(autoheal_execution, end - time.time())

    def get_autoheal_execution(self):
        executions = self.client.executions.list(
            deployment_id=self.deployment_id)
        for e in executions:
            if e.workflow_id == 'heal':
                return e
        return None

    execute_workflow_trigger = 'cloudify.policies.triggers.execute_workflow'
    workflow_parameters = {
        'node_instance_id': {'get_property': ['SELF', 'node_id']},
        'diagnose_value': {'get_property': ['SELF', 'diagnose']},
    }
    autoheal_group_yaml = {
        'autohealing_group': {
            'members': ['nodejs_host'],
            'policies': {
                'simple_autoheal_policy': {
                    'type': 'cloudify.policies.types.host_failure',
                    'properties': {'service': ['cpu.total.system']},
                    'triggers': {
                        'auto_heal_trigger': {
                            'type': execute_workflow_trigger,
                            'parameters': {
                                'workflow': 'heal',
                                'workflow_parameters': workflow_parameters
                            }
                        }
                    }
                }
            }
        }
    }
