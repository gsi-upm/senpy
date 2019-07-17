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

import noop
from senpy.plugins import SentimentPlugin


class NoOp(SentimentPlugin):
    '''This plugin does nothing. Literally nothing.'''

    version = 0

    def analyse_entry(self, entry, *args, **kwargs):
        yield entry

    def test(self):
        print(dir(noop))
        super(NoOp, self).test()

    test_cases = [{
        'entry': {
            'nif:isString': 'hello'
        },
        'expected': {
            'nif:isString': 'hello'
        }
    }]
