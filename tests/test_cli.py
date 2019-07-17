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

import logging
from functools import partial

logger = logging.getLogger(__name__)

from unittest import TestCase
from senpy.cli import main_function
from senpy.models import Error


class CLITest(TestCase):
    def test_basic(self):
        self.assertRaises(Error, partial(main_function, []))

        res = main_function(['--input', 'test', '--algo', 'sentiment-random',
                             '--with-parameters'])
        assert res.parameters['input'] == 'test'
        assert 'sentiment-random' in res.parameters['algorithm']
        assert res.parameters['input'] == 'test'
