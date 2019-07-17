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

from senpy.testing import patch_requests
from senpy.client import Client
from senpy.models import Results, Plugins, Error
from senpy.plugins import AnalysisPlugin


class ModelsTest(TestCase):
    def setUp(self):
        self.host = '0.0.0.0'
        self.port = 5000

    def test_client(self):
        endpoint = 'http://dummy/'
        client = Client(endpoint)
        with patch_requests('http://dummy/', Results()):
            resp = client.analyse('hello')
            assert isinstance(resp, Results)
        with patch_requests('http://dummy/', Error('Nothing')):
            try:
                client.analyse(input='hello', algorithm='NONEXISTENT')
                raise Exception('Exceptions should be raised. This is not golang')
            except Error:
                pass

    def test_client_post(self):
        endpoint = 'http://dummy/'
        client = Client(endpoint)
        with patch_requests('http://dummy/', Results()):
            resp = client.analyse('hello')
            assert isinstance(resp, Results)
        with patch_requests('http://dummy/', Error('Nothing'), method='POST'):
            try:
                client.analyse(input='hello', method='POST', algorithm='NONEXISTENT')
                raise Exception('Exceptions should be raised. This is not golang')
            except Error:
                pass

    def test_plugins(self):
        endpoint = 'http://dummy/'
        client = Client(endpoint)
        plugins = Plugins()
        p1 = AnalysisPlugin({'name': 'AnalysisP1', 'version': 0, 'description': 'No'})
        plugins.plugins = [p1, ]
        with patch_requests('http://dummy/plugins', plugins):
            response = client.plugins()
            assert isinstance(response, dict)
            assert len(response) == 1
            assert "AnalysisP1" in response
