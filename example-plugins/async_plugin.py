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

from senpy import AnalysisPlugin

import multiprocessing


def _train(process_number):
    return process_number


class Async(AnalysisPlugin):
    '''An example of an asynchronous module'''
    author = '@balkian'
    version = '0.2'
    sync = False

    def _do_async(self, num_processes):
        pool = multiprocessing.Pool(processes=num_processes)
        values = sorted(pool.map(_train, range(num_processes)))

        return values

    def activate(self):
        self.value = self._do_async(4)

    def analyse_entry(self, entry, params):
        values = self._do_async(2)
        entry.async_values = values
        yield entry

    test_cases = [
        {
            'input': 'any',
            'expected': {
                'async_values': [0, 1]
            }
        }
    ]
