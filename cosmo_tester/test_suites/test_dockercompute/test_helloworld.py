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

from cosmo_tester.test_suites.test_dockercompute import DockerComputeTestCase
from cosmo_tester.test_suites.test_blueprints.hello_world_bash_test import (
    AbstractHelloWorldTest,
    clone_hello_world)


class DockerComputeHelloWorldTest(DockerComputeTestCase,
                                  AbstractHelloWorldTest):

    def test_dockercompute_hello_world(self):
        self.repo_dir = clone_hello_world(self.workdir)
        blueprint_file = 'dockercompute-blueprint.yaml'
        self.blueprint_yaml = self.repo_dir / blueprint_file
        shutil.copy(self.blueprint_resource_path(
            'helloworld/{0}'.format(blueprint_file)),
            self.blueprint_yaml)
        self.add_plugin_yaml_to_blueprint()
        self.install(fetch_state=False)
        self.assert_events()
        self.assert_deployment_monitoring_data_exists()

        url = 'http://{0}:8080'.format(self.ip('vm'))

        def web_server_request():
            return self.request(url, connect_timeout=1)

        response = self.repetitive(web_server_request)
        self.assertIn('http_web_server', response)
        self.execute_uninstall(delete_deployment_and_blueprint=True)
        self.assertRaises(RuntimeError, web_server_request)


class StubTest(AbstractHelloWorldTest):

    def stub_test(self):
        pass
