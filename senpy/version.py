import os
import logging

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(__file__)
DEFAULT_FILE = os.path.join(ROOT, 'VERSION')


def read_version(versionfile=DEFAULT_FILE):
    with open(versionfile) as f:
        return f.read().strip()


__version__ = read_version()
