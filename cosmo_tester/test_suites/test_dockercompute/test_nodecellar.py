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

import shutil

from cosmo_tester.framework.git_helper import clone
from cosmo_tester.test_suites.test_dockercompute import DockerComputeTestCase
from cosmo_tester.test_suites.test_blueprints.nodecellar_test import (
    NodecellarAppTest)


class DockerComputeNodeCellarTest(DockerComputeTestCase, NodecellarAppTest):

    def test_dockercompute_nodecellar(self):
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
        self.execute_uninstall(deployment_id=self.test_id,
                               delete_deployment_and_blueprint=True)
        self.assertRaises(RuntimeError, self.request, url,
                          connect_timeout=connect_timeout)
