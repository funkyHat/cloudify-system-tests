########
# Copyright (c) 2015 GigaSpaces Technologies Ltd. All rights reserved
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

import json
import os
import shutil
import subprocess
import tempfile
import time

from cosmo_tester.framework import git_helper as git

from requests import ConnectionError
from cloudify_rest_client.exceptions import CloudifyClientError
from cosmo_tester.framework.util import create_rest_client
from cloudify.workflows import local
from cloudify_cli import constants as cli_constants
import boto.ec2
from novaclient.v2 import client as novaclient

DEFAULT_IMAGE_BAKERY_REPO_URL = 'https://github.com/' \
                                'cloudify-cosmo/cloudify-image-bakery.git'
DEFAULT_PACKER_URL = 'https://releases.hashicorp.com/packer/' \
                     '0.10.0/packer_0.10.0_linux_amd64.zip'
DEFAULT_PACKER_FILE = 'cloudify.json'
DEFAULT_CLOUDIFY_VERSION = '3.3.1'
DEFAULT_AMI = "ami-91feb7fb"
DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_AWS_INSTANCE_TYPE = 'm3.large'
SUPPORTED_ENVS = [
    'aws',
    'openstack',
]


class AbstractPackerTest(object):
    def setUp(self):
        self.conf = self.env.cloudify_config

        self.aws_hello_world_test_config_inputs = {
            'user_ssh_key': self.conf['aws_ssh_keypair_name'],
            'agents_user': self.conf.get('aws_agents_user', 'ubuntu'),
            'aws_access_key': self.conf['aws_access_key'],
            'aws_secret_key': self.conf['aws_secret_key'],
        }

    def _find_images(self):
        finders = {
            'aws': self._find_image_aws,
            'openstack': self._find_image_openstack,
        }
        for environment in self.images.keys():
            self.images[environment] = finders[environment]()

    def delete_images(self):
        deleters = {
            'aws': self._delete_image_aws,
            'openstack': self._delete_image_openstack,
        }

        for environment in self.images.keys():
            deleters[environment](self.images[environment])

    def _get_conn_aws(self):
        return boto.ec2.EC2Connection(
            aws_access_key_id=self.env.cloudify_config[
                'aws_access_key'],
            aws_secret_access_key=self.env.cloudify_config[
                'aws_secret_key'],
        )

    def _find_image_aws(self):
        conn = self._get_conn_aws()

        image_id = None

        images = conn.get_all_images(owners='self')

        for image in images:
            if image.name.startswith(self.name_prefix):
                image_id = image.id
                break

        return image_id

    def deploy_image_aws(self):
        blueprint_path = self.copy_blueprint('aws-vpc-start-vm')
        self.aws_blueprint_yaml = os.path.join(
            blueprint_path,
            'blueprint.yaml'
        )

        self.aws_inputs = {
            'image_id': self.images['aws'],
            'instance_type': self.build_inputs['aws_instance_type'],
            'vpc_id': self.env.cloudify_config['aws_vpc_id'],
            'vpc_subnet_id': self.env.cloudify_config['aws_subnet_id'],
            'server_name': 'marketplace-system-test-manager',
            'aws_access_key_id': self.build_inputs['aws_access_key'],
            'aws_secret_access_key': self.build_inputs['aws_secret_key'],
            'ec2_region_name': self.build_inputs['aws_region'],
        }

        self.logger.info('initialize local env for running the '
                         'blueprint that starts a vm')
        self.aws_manager_env = local.init_env(
            self.aws_blueprint_yaml,
            inputs=self.aws_inputs,
            name=self._testMethodName,
            ignored_modules=cli_constants.IGNORED_LOCAL_WORKFLOW_MODULES
        )

        self.logger.info('starting vm to serve as the management vm')
        self.aws_manager_env.execute('install',
                                     task_retries=10,
                                     task_retry_interval=30)

        outputs = self.aws_manager_env.outputs()
        self.aws_manager_public_ip = outputs[
            'simple_vm_public_ip_address'
        ]

        self.addCleanup(self._undeploy_image_aws)

    def _undeploy_image_aws(self):
        # Private method as it is used for cleanup
        self.aws_manager_env.execute('uninstall',
                                     task_retries=40,
                                     task_retry_interval=30)

    def _delete_image_aws(self, image_id):
        conn = self._get_conn_aws()
        image = conn.get_all_images(image_ids=[image_id])[0]
        image.deregister()

    def _get_conn_openstack(self):
        return novaclient.Client(
            username=self.env.cloudify_config['keystone_username'],
            api_key=self.env.cloudify_config['keystone_password'],
            auth_url=self.env.cloudify_config['keystone_url'],
            project_id=self.env.cloudify_config['keystone_tenant_name'],
            region=self.env.cloudify_config['region'],
        )

    def _find_image_openstack(self):
        conn = self._get_conn_openstack()

        image_id = None

        # Tenant ID does not appear to be populated until another action has
        # been taken, so we will make a call to cause it to be populated.
        # We use floating IPs as this shouldn't be a huge amount of data.
        # We could try making a call that will return nothing, but those may
        # raise exceptions so we will trust that list should not do so.
        conn.floating_ips.list()
        my_tenant_id = conn.client.tenant_id

        images = conn.images.list()
        self.logger.info('Images from platform: %s' % images)
        images = [image.to_dict() for image in images]
        self.logger.info('Tenant ID: %s' % my_tenant_id)
        for image in images:
            self.logger.info(image['metadata'])
        # Get just the images belonging to this tenant
        images = [
            image for image in images
            if 'owner_id' in image['metadata'].keys() and
            # 'and' on previous line due to PEP8
            image['metadata']['owner_id'] == my_tenant_id
        ]
        self.logger.info('All images: %s' % images)
        self.logger.info('Searching by prefix: %s' % self.name_prefix)
        # Filter for the prefix
        for image in images:
            self.logger.info('Checking %s...' % image['name'])
            if image['name'].startswith(self.name_prefix):
                self.logger.info('Correct image, with ID: %s' % image['id'])
                image_id = image['id']
                break

        return image_id

    def deploy_image_openstack(self):
        blueprint_path = self.copy_blueprint('openstack-start-vm')
        self.openstack_blueprint_yaml = os.path.join(
            blueprint_path,
            'blueprint.yaml'
        )
        self.prefix = 'packer-system-test-{0}'.format(self.test_id)

        self.openstack_inputs = {
            'prefix': self.prefix,
            'external_network': self.env.cloudify_config[
                'openstack_external_network_name'],
            'os_username': self.env.cloudify_config['keystone_username'],
            'os_password': self.env.cloudify_config['keystone_password'],
            'os_tenant_name': self.env.cloudify_config[
                'keystone_tenant_name'],
            'os_region': self.env.cloudify_config['region'],
            'os_auth_url': self.env.cloudify_config['keystone_url'],
            'image_id': self.images['openstack'],
            'flavor': self.env.cloudify_config[
                'openstack_marketplace_flavor'],
            'key_pair_path': '{0}/{1}-keypair.pem'.format(self.workdir,
                                                          self.prefix)
        }

        self.logger.info('initialize local env for running the '
                         'blueprint that starts a vm')
        self.openstack_manager_env = local.init_env(
            self.openstack_blueprint_yaml,
            inputs=self.openstack_inputs,
            name=self._testMethodName,
            ignored_modules=cli_constants.IGNORED_LOCAL_WORKFLOW_MODULES
        )

        self.logger.info('starting vm to serve as the management vm')
        self.openstack_manager_env.execute('install',
                                           task_retries=10,
                                           task_retry_interval=30)

        outputs = self.openstack_manager_env.outputs()
        self.openstack_manager_public_ip = outputs[
            'simple_vm_public_ip_address'
        ]
        self.openstack_manager_private_ip = outputs[
            'simple_vm_private_ip_address'
        ]

        self.addCleanup(self._undeploy_image_openstack)

    def _undeploy_image_openstack(self):
        # Private method as it is used for cleanup
        self.openstack_manager_env.execute('uninstall',
                                           task_retries=40,
                                           task_retry_interval=30)

    def _delete_image_openstack(self, image_id):
        conn = self._get_conn_openstack()
        image = conn.images.find(id=image_id)
        image.delete()

    def _get_packer(self, destination):
        packer_url = self.env.cloudify_config.get(
            'packer_url',
            DEFAULT_PACKER_URL
        )
        wget_command = [
            'wget',
            packer_url
        ]
        wget_status = subprocess.call(
            wget_command,
            cwd=destination,
        )
        assert wget_status == 0

        unzip_command = [
            'unzip',
            os.path.split(packer_url)[1],
        ]
        unzip_status = subprocess.call(
            unzip_command,
            cwd=destination,
        )
        assert unzip_status == 0

        return os.path.join(destination, 'packer')

    def _get_marketplace_image_bakery_repo(self):
        self.base_temp_dir = tempfile.mkdtemp()

        url = self.env.cloudify_config.get(
            'image_bakery_url',
            DEFAULT_IMAGE_BAKERY_REPO_URL
        )

        git.clone(
            url=url,
            basedir=self.base_temp_dir,
            branch=self.env.cloudify_config.get('image_bakery_branch'),
        )

        self.addCleanup(self.clean_temp_dir)

        repo_path = os.path.join(
            self.base_temp_dir,
            'git',
            'cloudify-image-bakery',
        )
        return repo_path

    def _build_inputs(self, destination_path, name_prefix, secure=True):
        openstack_url = self.env.cloudify_config.get('keystone_url')
        if openstack_url is not None:
            # TODO: Do a join on this if the URL doesn't have 2.0 already
            openstack_url += '/v2.0/'
        else:
            openstack_url = 'OPENSTACK IDENTITY ENDPOINT NOT SET'
        # Provide 'not set' defaults for most to allow for running e.g. just
        # the openstack tests without complaining about lack of aws settings
        self.build_inputs = {
            "name_prefix": name_prefix,
            "cloudify_version": self.env.cloudify_config.get(
                'marketplace_cloudify_version',
                DEFAULT_CLOUDIFY_VERSION
            ),
            "aws_access_key": self.env.cloudify_config.get(
                'aws_access_key',
                'AWS ACCESS KEY NOT SET'
            ),
            "aws_secret_key": self.env.cloudify_config.get(
                'aws_secret_key',
                'AWS SECRET KEY NOT SET'
            ),
            "aws_source_ami": self.env.cloudify_config.get(
                'marketplace_source_ami',
                DEFAULT_AMI
            ),
            "aws_region": self.env.cloudify_config.get(
                'aws_region',
                DEFAULT_AWS_REGION
            ),
            "aws_instance_type": self.env.cloudify_config.get(
                'aws_instance_type',
                DEFAULT_AWS_INSTANCE_TYPE
            ),
            "openstack_ssh_keypair_name": self.env.cloudify_config.get(
                'openstack_ssh_keypair',
                'OPENSTACK SSH KEYPAIR NOT SET'
            ),
            "openstack_availability_zone": self.env.cloudify_config.get(
                'openstack_marketplace_availability_zone',
                'OPENSTACK AVAILABILITY ZONE NOT SET'
            ),
            "openstack_image_flavor": self.env.cloudify_config.get(
                'openstack_marketplace_flavor',
                'OPENSTACK FLAVOR NOT SET'
            ),
            "openstack_identity_endpoint": openstack_url,
            "openstack_source_image_id": self.env.cloudify_config.get(
                'openstack_marketplace_source_image',
                'OPENSTACK SOURCE IMAGE NOT SET'
            ),
            "openstack_username": self.env.cloudify_config.get(
                'keystone_username',
                'OPENSTACK USERNAME NOT SET'
            ),
            "openstack_password": self.env.cloudify_config.get(
                'keystone_password',
                'OPENSTACK PASSWORD NOT SET'
            ),
            "openstack_tenant_name": self.env.cloudify_config.get(
                'keystone_tenant_name',
                'OPENSTACK TENANT NAME NOT SET'
            ),
            "openstack_floating_ip_pool_name": self.env.cloudify_config.get(
                'openstack_floating_ip_pool_name',
                'OPENSTACK FLOATING IP POOL NOT SET'
            ),
            "openstack_network": self.env.cloudify_config.get(
                'openstack_network',
                'OPENSTACK NETWORK NOT SET'
            ),
            "openstack_security_group": self.env.cloudify_config.get(
                'openstack_security_group',
                'OPENSTACK SECURITY GROUP NOT SET'
            ),
            "cloudify_version": self.env.cloudify_config.get(
                'marketplace_cloudify_version',
                'master'
            ),
            "cloudify_manager_security_enabled":
                'true' if str(secure) else 'false',
        }
        inputs = json.dumps(self.build_inputs)
        with open(destination_path, 'w') as inputs_handle:
            inputs_handle.write(inputs)

    def build_with_packer(self,
                          name_prefix='marketplace-system-tests',
                          only=None,
                          secure=True):
        self.name_prefix = name_prefix
        if only is None:
            self.images = {environment: None for environment in SUPPORTED_ENVS}
        else:
            self.images = {only: None}

        self._check_for_images(should_exist=False)

        image_bakery_repo_path = self._get_marketplace_image_bakery_repo()

        marketplace_path = os.path.join(
            image_bakery_repo_path,
            'cloudify_marketplace',
        )

        packer_bin = self._get_packer(marketplace_path)

        inputs_file_name = 'system-test-inputs.json'
        self._build_inputs(
            destination_path=os.path.join(
                marketplace_path,
                inputs_file_name
            ),
            name_prefix=name_prefix,
            secure=secure,
        )

        # Build the packer command
        command = [
            packer_bin,
            'build',
            '--var-file={inputs}'.format(inputs=inputs_file_name),
        ]
        if only is not None:
            command.append('--only={only}'.format(only=only))
        command.append(self.env.cloudify_config.get(
            'packer_file',
            DEFAULT_PACKER_FILE
        ))

        # Run packer
        self.logger.info(command)
        build_status = subprocess.call(
            command,
            cwd=marketplace_path,
        )
        assert build_status == 0

        # A test on AWS failed due to no image being found despite the image
        # existing, so we will put a small delay here to reduce the chance of
        # that recurring
        # It would be nice if there were a better way to do this, but it
        # depends on the environment and maximum wait time is unclear
        time.sleep(15)

        self._check_for_images()

        self.addCleanup(self.delete_images)

    def _check_for_images(self, should_exist=True):
        self._find_images()
        for env, image in self.images.items():
            if should_exist:
                fail = 'Image for {env} not found!'.format(env=env)
                assert image is not None, fail
            else:
                fail = 'Image for {env} already exists!'.format(env=env)
                assert image is None, fail

    def clean_temp_dir(self):
        shutil.rmtree(self.base_temp_dir)

    def _delete_agents_keypair(self):
        conn = self._get_conn_aws()
        conn.delete_key_pair(key_name=self.aws_agents_keypair)

    def _delete_agents_secgroup(self):
        conn = self._get_conn_aws()
        sgs = conn.get_all_security_groups()
        candidate_sgs = [
            sg for sg in sgs
            if sg.name == self.aws_agents_secgroup and
            # 'and' is on previous line due to PEP8
            sg.vpc_id == self.env.cloudify_config['aws_vpc_id']
        ]
        if len(candidate_sgs) != 1:
            raise RuntimeError('Could not clean up agents security group')
        else:
            sg_id = candidate_sgs[0].id
            for sg in sgs:
                for rule in sg.rules:
                    groups = [grant.group_id for grant in rule.grants]
                    if sg_id in groups:
                        self._delete_sg_rule_reference(
                            security_group=sg,
                            proto=rule.ip_protocol,
                            from_port=rule.from_port,
                            to_port=rule.to_port,
                            source_sg=candidate_sgs[0],
                        )
            candidate_sgs[0].delete()

    def _delete_sg_rule_reference(self,
                                  security_group,
                                  from_port,
                                  to_port,
                                  source_sg,
                                  proto='tcp'):
        security_group.revoke(
            ip_protocol=proto,
            from_port=from_port,
            to_port=to_port,
            src_group=source_sg,
        )

    def get_public_ip(self, nodes_state):
        return self.aws_manager_public_ip

    @property
    def expected_nodes_count(self):
        return 4

    @property
    def host_expected_runtime_properties(self):
        return []

    @property
    def entrypoint_node_name(self):
        return 'host'

    @property
    def entrypoint_property_name(self):
        return 'ip'

    def _deploy_manager(self, secure=False, trust_all=False):
        self.build_with_packer(only='aws', secure=secure)
        self.deploy_image_aws()

        self.client = create_rest_client(
            self.aws_manager_public_ip,
            secure=secure,
            trust_all=trust_all,
        )

        response = {'status': None}
        attempt = 0
        max_attempts = 80
        while response['status'] != 'running':
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError('Manager did not start in time')
            else:
                time.sleep(3)
            try:
                response = self.client.manager.get_status()
            except CloudifyClientError:
                # Manager not fully ready
                pass
            except ConnectionError:
                # Timeout
                pass

        self.aws_agents_secgroup = self.conf.get(
            'system-tests-security-group-name',
            'marketplace-system-tests-security-group')
        self.aws_agents_keypair = self.conf.get(
            'system-tests-keypair-name',
            'marketplace-system-tests-keypair')

        self.aws_hello_world_test_config_inputs.update({
            'agents_security_group_name': self.aws_agents_secgroup,
            'agents_keypair_name': self.aws_agents_keypair,
            })
        if secure:
            # Need to add the external IP address to the generated cert
            self.aws_hello_world_test_config_inputs.update({
                'manager_names_and_ips': self.aws_manager_public_ip,
                })

        # Arbitrary sleep to wait for manager to actually finish starting as
        # otherwise we suffer timeouts in the next section
        # TODO: This would be better if it actually had some way of checking
        # the manager was fully up and we had a reasonable upper bound on how
        # long we should expect to wait for that
        time.sleep(90)

        # We have to retry this a few times, as even after the manager is
        # accessible we still see failures trying to create deployments
        deployment_created = False
        attempt = 0
        max_attempts = 40
        while not deployment_created:
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError('Manager not created in time')
            else:
                time.sleep(3)
            try:
                self.client.deployments.create(
                    blueprint_id='CloudifySettings',
                    deployment_id='config',
                    inputs=self.aws_hello_world_test_config_inputs,
                )
                self.addCleanup(self._delete_agents_secgroup)
                self.addCleanup(self._delete_agents_keypair)
                deployment_created = True
            except Exception as err:
                if attempt >= max_attempts:
                    raise err
                else:
                    self.logger.warn(
                        'Saw error {}. Retrying.'.format(str(err))
                    )

        attempt = 0
        max_attempts = 40
        execution_started = False
        while not execution_started:
            attempt += 1
            if attempt >= max_attempts:
                raise RuntimeError('Manager did not start in time')
            else:
                time.sleep(3)
            try:
                self.client.executions.start(
                    deployment_id='config',
                    workflow_id='install',
                )
                execution_started = True
            except Exception as err:
                if attempt >= max_attempts:
                    raise err
                else:
                    self.logger.warn(
                        'Saw error {}. Retrying.'.format(str(err))
                    )