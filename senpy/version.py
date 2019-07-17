#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

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
        return 'devel'


__version__ = read_version()
