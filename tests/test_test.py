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

from unittest import TestCase

import requests
import json
from senpy.testing import patch_requests
from senpy.models import Results

ENDPOINT = 'http://invalid.com'


class TestTest(TestCase):
    def test_patch_text(self):
        with patch_requests(ENDPOINT, 'hello'):
            r = requests.get(ENDPOINT)
            assert r.text == 'hello'

    def test_patch_json(self):
        r = Results()
        with patch_requests(ENDPOINT, r):
            res = requests.get(ENDPOINT)
            assert res.text == json.dumps(r.jsonld())
            js = res.json()
            assert js
            assert js['@type'] == r['@type']

    def test_patch_dict(self):
        r = {'nothing': 'new'}
        with patch_requests(ENDPOINT, r):
            res = requests.get(ENDPOINT)
            assert res.text == json.dumps(r)
            js = res.json()
            assert js
            assert js['nothing'] == 'new'
