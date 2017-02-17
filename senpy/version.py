import os
import subprocess
import logging

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(__file__)
DEFAULT_FILE = os.path.join(ROOT, 'VERSION')


def git_version():
    try:
        res = subprocess.check_output(['git', 'describe',
                                       '--tags', '--dirty']).decode('utf-8')
        return res.strip()
    except subprocess.CalledProcessError:
        return None


def read_version(versionfile=DEFAULT_FILE):
    with open(versionfile) as f:
        return f.read().strip()


def write_version(version, versionfile=DEFAULT_FILE):
    version = version or git_version()
    if not version:
        raise ValueError('You need to provide a valid version')
    with open(versionfile, 'w') as f:
        f.write(version)


__version__ = git_version() or read_version()
write_version(__version__)
