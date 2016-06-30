import os
from subprocess import check_output

import pytest


class GitHelper(object):
    def __init__(self, workdir):
        self.workdir = workdir

    def _exec(self, command, repo_path):
        prepared_command = ['git']
        prepared_command.extend(command)

        repo_path = os.path.join(self.workdir, repo_path)

        return check_output(prepared_command, cwd=repo_path)

    def clone(self, repository, clone_to=None):
        if not clone_to:
            # Clone to the repo name if no clone_to is provided
            clone_to = os.path.split(repository)[-1].rstrip('.git')

        path = os.path.join(self.workdir, clone_to)
        # This might want to be an is_dir check to give better error messages
        if not os.path.exists(path):
            os.mkdir(path)

        # We clone to 'current dir' in the repo path to simplify self._exec
        return self._exec(['clone', repository, '.'], repo_path=clone_to)

    def checkout(self, repo_path, checkout):
        return self._exec(['checkout', checkout], repo_path=repo_path)


@pytest.fixture
def githelper(tmpdir):
    return GitHelper(str(tmpdir))


@pytest.fixture(scope='session')
def persistentgithelper(tmpdir_factory):
    return GitHelper(str(tmpdir_factory.mktemp('githelper')))


try:
    from pytest_bdd import given
except ImportError:
    pass
else:
    from pytest_bdd.parsers import parse

    @given(parse("I clone the repo '{repo}' into '{dir}'"))
    def clone_git_repo(repo, dir, githelper):
        githelper.clone(repo, dir)
        return os.path.join(githelper.workdir, dir)

    @given(parse("I check out the branch '{branch}'"))
    def check_out_branch(githelper, clone_git_repo, branch):
        githelper.checkout(clone_git_repo, branch)
        return os.path.join(clone_git_repo)
