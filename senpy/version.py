import os
import logging

logger = logging.getLogger(__name__)

ROOT = os.path.dirname(__file__)
DEFAULT_FILE = os.path.join(ROOT, 'VERSION')


def read_version(versionfile=DEFAULT_FILE):
    try:
        with open(versionfile) as f:
            return f.read().strip()
    except IOError:  # pragma: no cover
        logger.error('Running an unknown version of senpy. Be careful!.')
        return '0.0'


__version__ = read_version()
