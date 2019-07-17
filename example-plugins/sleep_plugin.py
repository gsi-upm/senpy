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

from senpy.plugins import AnalysisPlugin
from time import sleep


class Sleep(AnalysisPlugin):
    '''Dummy plugin to test async'''
    author = "@balkian"
    version = "0.2"
    timeout = 0.05
    extra_params = {
        "timeout": {
            "@id": "timeout_sleep",
            "aliases": ["timeout", "to"],
            "required": False,
            "default": 0
        }
    }

    def activate(self, *args, **kwargs):
        sleep(self.timeout)

    def analyse_entry(self, entry, params):
        sleep(float(params.get("timeout", self.timeout)))
        yield entry

    def test(self):
        pass
