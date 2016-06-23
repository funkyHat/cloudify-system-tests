from cloudify_tester.helpers.git import GitHelper
from cloudify_tester.helpers.cfy import CfyHelper
from cloudify_tester.helpers.pip import PipHelper

from subprocess import check_call
import tempfile


class DangerousBugError(Exception):
    pass


class TestEnvironment(object):
    cfy = None
    git = None
    pip = None
    _cleanups = []

    def start(self, cloudify_version=None):
        self.workdir = tempfile.mkdtemp()
        self.cfy = CfyHelper(workdir=self.workdir)
        self.git = GitHelper(workdir=self.workdir)
        self.pip = PipHelper(workdir=self.workdir)

        check_call(['virtualenv', '.'], cwd=self.workdir)
        if cloudify_version:
            cloudify = 'cloudify=={version}'.format(
                version=cloudify_version
            )
        else:
            cloudify = 'cloudify'
        self.pip.install(cloudify)

    def add_cleanup(self, function, args=None, kwargs=None):
        cleanup = {
            'function': function,
        }
        if args is not None:
            cleanup['args'] = args
        if kwargs is not None:
            cleanup['kwargs'] = kwargs
        self._cleanups.append(cleanup)

    def teardown(self):
        for cleanup in self._cleanups:
            func = cleanup['function']
            args = cleanup.get('args', [])
            kwargs = cleanup.get('kwargs', {})
            func(*args, **kwargs)

        # This will break on a Mac (and Windows), so should have a better
        # check, but it probably wants something just to avoid major pain on
        # a single typo in a later commit
        if not self.workdir.startswith('/tmp/'):
            raise DangerousBugError(
                'An attempt was made to delete something not in a temp '
                'directory. Target was: {path}'.format(
                    path=workdir,
                )
            )
        else:
            check_call(['rm', '-rf', self.workdir])
