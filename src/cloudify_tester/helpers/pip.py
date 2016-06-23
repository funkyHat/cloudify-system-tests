import os
from subprocess import check_output

import yaml


class PipHelper(object):
    def __init__(self, workdir):
        self.workdir = workdir

    def _exec(self, command, install_plugins=False):
        prepared_command = ['bin/pip']
        prepared_command.extend(command)
        check_output(prepared_command, cwd=self.workdir)

    def install(self, packages):
        if not isinstance(packages, list):
            packages = [packages]
        command = ['install']
        command.extend(packages)
        self._exec(command)
