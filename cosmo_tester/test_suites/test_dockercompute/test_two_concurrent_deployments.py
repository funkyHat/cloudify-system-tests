########
# Copyright (c) 2014 GigaSpaces Technologies Ltd. All rights reserved
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

import threading
import shutil
import Queue

from cosmo_tester.test_suites.test_dockercompute import DockerComputeTestCase
from cosmo_tester.test_suites.test_blueprints.hello_world_bash_test import (
    clone_hello_world)


class TwoDeploymentsTest(DockerComputeTestCase):

    def test_two_concurrent_deployments(self):
        blueprint_file = 'dockercompute-blueprint.yaml'
        self.blueprint_path = clone_hello_world(self.workdir)
        self.blueprint_yaml = self.blueprint_path / blueprint_file
        shutil.copy(self.blueprint_resource_path(
            'helloworld/{0}'.format(blueprint_file)),
            self.blueprint_yaml)
        self.add_plugin_yaml_to_blueprint()
        count = 2
        deployments = [self.Deployment(self, i) for i in range(count)]
        for deployment in deployments:
            deployment.run()
        for deployment in deployments:
            deployment.wait_for()

    def run_deployment(self, index, queue):
        try:
            blueprint_id = '{}_{}'.format(self.test_id, index)
            deployment_id = blueprint_id
            self.install(blueprint_id=blueprint_id,
                         deployment_id=deployment_id,
                         fetch_state=False)
            ip = self.ip('vm', deployment_id=deployment_id)
            url = 'http://{0}:8080'.format(ip)
            response = self.request(url, connect_timeout=1)
            self.assertIn('http_web_server', response)
            self.execute_uninstall(deployment_id=deployment_id,
                                   delete_deployment_and_blueprint=True)
        except Exception, e:
            queue.put(e)
        else:
            queue.put(True)

    class Deployment(object):

        def __init__(self, test_case, index):
            self.index = index
            self.queue = Queue.Queue(maxsize=1)
            self.test_case = test_case
            self.thread = threading.Thread(target=test_case.run_deployment,
                                           args=(self.index, self.queue))

        def run(self):
            self.thread.start()

        def wait_for(self):
            result = self.queue.get(timeout=1800)
            if isinstance(result, Exception):
                raise result
