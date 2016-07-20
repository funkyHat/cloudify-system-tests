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

import csv
from StringIO import StringIO
import shutil

from cosmo_tester.framework.git_helper import clone
from cosmo_tester.test_suites.test_dockercompute import DockerComputeTestCase
from cosmo_tester.test_suites.test_blueprints.nodecellar_test import (
    NodecellarAppTest)


class DockerComputeNodeCellarScaleTest(DockerComputeTestCase,
                                       NodecellarAppTest):

    def test_dockercompute_nodecellar_scale(self):
        blueprint_file = 'dockercompute-haproxy-blueprint.yaml'
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
        ip = self.ip('haproxy_frontend_host')
        url = 'http://{0}:{1}/wines'.format(ip, self.nodecellar_port)
        response = self.request(url, json=True,
                                connect_timeout=connect_timeout)
        self.assertEqual(list, type(response))
        self.assertGreater(len(response), 1)

        self._scale(delta=1)
        self.post_scale_assertions(expected_instances=2, ip=ip)

        self._scale(delta=-1)
        self.post_scale_assertions(expected_instances=1, ip=ip)

        self.execute_uninstall(deployment_id=self.test_id,
                               delete_deployment_and_blueprint=True)
        self.assertRaises(RuntimeError, self.request, url,
                          connect_timeout=connect_timeout)

    def post_scale_assertions(self, expected_instances, ip):
        self.assert_nodecellar_working(
            expected_number_of_backends=expected_instances, ip=ip)

    def _scale(self, delta):
        self.cfy.execute_workflow(
            'scale', self.test_id,
            parameters=dict(scalable_entity_name='nodecellar',
                            delta=delta,
                            scale_compute=True))

    def assert_nodecellar_working(self, expected_number_of_backends, ip):
        initial_stats = self._read_haproxy_stats(ip)
        number_of_backends = len(initial_stats)
        self.assertEqual(expected_number_of_backends, number_of_backends)
        for count in initial_stats.values():
            self.assertEqual(0, count)
        for i in range(1, number_of_backends + 1):
            url = 'http://{0}:{1}/wines'.format(ip, self.nodecellar_port)
            self.request(url, connect_timeout=1)
            stats = self._read_haproxy_stats(ip)
            active_backends = [b for b, count in stats.items() if count == 1]
            self.assertEqual(i, len(active_backends))

    def _read_haproxy_stats(self, ip):
        url = 'http://admin:password@{0}:9000/haproxy_stats;csv'.format(ip)
        csv_data = self.request(url)
        buff = StringIO(csv_data)
        parsed_csv_data = list(csv.reader(buff))
        headers = parsed_csv_data[0]
        structured_csv_data = [dict(zip(headers, row))
                               for row in parsed_csv_data]
        return dict([(struct['svname'], int(struct['stot']))
                     for struct in structured_csv_data
                     if struct['# pxname'] == 'servers' and
                     struct['svname'] != 'BACKEND'])

    @property
    def repo_branch(self):
        return 'dockercompute-system-tests'
