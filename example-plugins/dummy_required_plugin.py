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

from senpy import AnalysisPlugin, easy


class DummyRequired(AnalysisPlugin):
    '''This is a dummy self-contained plugin'''
    author = '@balkian'
    version = '0.1'
    extra_params = {
        'example': {
            'description': 'An example parameter',
            'required': True,
            'options': ['a', 'b']
        }
    }

    def analyse_entry(self, entry, params):
        entry['nif:isString'] = entry['nif:isString'][::-1]
        entry.reversed = entry.get('reversed', 0) + 1
        yield entry

    test_cases = [{
        'entry': {
            'nif:isString': 'Hello',
        },
        'should_fail': True
    }, {
        'entry': {
            'nif:isString': 'Hello',
        },
        'params': {
            'example': 'a'
        },
        'expected': {
            'nif:isString': 'olleH'
        }
    }]


if __name__ == '__main__':
    easy()
