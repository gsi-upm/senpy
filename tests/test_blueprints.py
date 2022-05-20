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

from senpy.extensions import Senpy
from senpy import models
from flask import Flask
from unittest import TestCase
from itertools import product


def check_dict(indic, template):
    return all(item in indic.items() for item in template.items())


def parse_resp(resp):
    return models.from_json(resp.data.decode('utf-8'))


class BlueprintsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up only once, and re-use in every individual test"""
        cls.app = Flask("test_extensions")
        cls.client = cls.app.test_client()
        cls.senpy = Senpy(default_plugins=True)
        cls.senpy.init_app(cls.app)
        cls.dir = os.path.join(os.path.dirname(__file__), "..")
        cls.senpy.add_folder(cls.dir)
        cls.senpy.activate_all()
        cls.senpy.default_plugin = 'Dummy'

    def setUp(self):
        self.app.config['TESTING'] = True  # Tell Flask not to catch Exceptions

    def assertCode(self, resp, code):
        self.assertEqual(resp.status_code, code)

    def test_playground(self):
        resp = self.client.get("/")
        assert "main.js" in resp.get_data(as_text=True)

    def test_home(self):
        """
        Calling with no arguments should ask the user for more arguments
        """
        self.app.config['TESTING'] = False  # Errors are expected in this case
        resp = self.client.get("/api/")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug(js)
        assert js["status"] == 400
        atleast = {
            "status": 400,
            "message": "Missing or invalid parameters",
        }
        assert check_dict(js, atleast)

    def test_analysis(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        resp = self.client.get("/api/?i=My aloha mohame&verbose")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js
        assert len(js['activities']) == 1

    def test_analysis_post(self):
        """
        The results for a POST request should be the same as for a GET request.
        """
        resp = self.client.post("/api/", data={'i': 'My aloha mohame',
                                               'algorithm': 'sentiment-random',
                                               'verbose': True})
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js
        assert len(js['activities']) == 1

    def test_analysis_extra(self):
        """
        Extra params that have a default should use it
        """
        resp = self.client.get("/api/?i=My aloha mohame&algo=Dummy&with-parameters=true")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js

    def test_analysis_extra_required(self):
        """
        Extra params that have a required argument that does not
        have a default should raise an error.
        """
        self.app.config['TESTING'] = False  # Errors are expected in this case
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired&example=notvalid")
        self.assertCode(resp, 400)
        self.app.config['TESTING'] = True
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired&example=a")
        self.assertCode(resp, 200)

    def test_analysis_url(self):
        """
        The algorithm can also be specified as part of the URL
        """
        self.app.config['TESTING'] = False  # Errors are expected in this case
        resp = self.client.get("/api/DummyRequired?i=My aloha mohame")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)
        resp = self.client.get("/api/DummyRequired?i=My aloha mohame&example=notvalid")
        self.assertCode(resp, 400)
        resp = self.client.get("/api/DummyRequired?i=My aloha mohame&example=a")
        self.assertCode(resp, 200)

    def test_analysis_chain(self):
        """
        More than one algorithm can be specified. Plugins will then be chained
        """
        resp = self.client.get("/api/Dummy?i=My aloha mohame&verbose")
        js = parse_resp(resp)
        assert len(js['activities']) == 1
        assert js['entries'][0]['nif:isString'] == 'My aloha mohame'[::-1]

        resp = self.client.get("/api/Dummy/Dummy?i=My aloha mohame&verbose")
        # Calling dummy twice, should return the same string
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert len(js['activities']) == 2
        assert js['entries'][0]['nif:isString'] == 'My aloha mohame'

        resp = self.client.get("/api/Dummy+Dummy?i=My aloha mohame&verbose")
        # Same with pluses instead of slashes
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert len(js['activities']) == 2
        assert js['entries'][0]['nif:isString'] == 'My aloha mohame'

    def test_analysis_chain_required(self):
        """
        If a parameter is required and duplicated (because two plugins require it), specifying
        it once should suffice
        """
        resp = self.client.get(('/api/DummyRequired/DummyRequired?'
                                'i=My aloha mohame&example=a&verbose'))
        js = parse_resp(resp)
        assert len(js['activities']) == 2
        assert js['entries'][0]['nif:isString'] == 'My aloha mohame'
        assert js['entries'][0]['reversed'] == 2

    def test_requirements_chain_help(self):
        '''The extra parameters of each plugin should be merged if they are in a chain '''
        resp = self.client.get("/api/split/DummyRequired?help=true")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert 'valid_parameters' in js
        vp = js['valid_parameters']
        assert 'example' in vp
        assert 'delimiter' in vp

    def test_requirements_chain_repeat_help(self):
        '''
        If a plugin appears several times in a chain, there should be a way to set different
        parameters for each.
        '''
        resp = self.client.get("/api/split/split?help=true")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert 'valid_parameters' in js
        vp = js['valid_parameters']
        assert 'delimiter' in vp

        resp = self.client.get("/api/split/split?help=true&verbose=false")
        js = parse_resp(resp)
        vp = js['valid_parameters']
        assert len(vp.keys()) == 1

    def test_requirements_chain(self):
        """
        It should be possible to specify different parameters for each step in the chain.
        """
        # First, we split by sentence twice. Each call should generate 3 additional entries
        # (one per sentence in the original).
        resp = self.client.get('/api/split/split?i=The first sentence. The second sentence.'
                               '\nA new paragraph&delimiter=sentence&verbose')
        js = parse_resp(resp)
        assert len(js['activities']) == 2
        assert len(js['entries']) == 7

        # Now, we split by sentence. This produces 3 additional entries.
        # Then, we split by paragraph. This should create 2 additional entries (One per paragraph
        # in the original text)
        resp = self.client.get('/api/split/split?i=The first sentence. The second sentence.'
                               '\nA new paragraph&0.delimiter=sentence'
                               '&1.delimiter=paragraph&verbose')
        # Calling dummy twice, should return the same string
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert len(js['activities']) == 2
        assert len(js['entries']) == 6

    def test_error(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        self.app.config['TESTING'] = False  # Errors are expected in this case
        resp = self.client.get("/api/?i=My aloha mohame&algo=DOESNOTEXIST")
        self.assertCode(resp, 404)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)

    def test_list(self):
        """ List the plugins """
        resp = self.client.get("/api/plugins/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert 'plugins' in js
        plugins = js['plugins']
        assert len(plugins) > 1
        assert any(x['name'] == 'dummy' for x in plugins)
        assert "@context" in js

    def test_headers(self):
        for i, j in product(["/api/plugins/?nothing=", "/api/?i=test&"],
                            ["in-headers"]):
            resp = self.client.get("%s" % (i))
            js = parse_resp(resp)
            assert "@context" in js
            resp = self.client.get("%s&%s=0" % (i, j))
            js = parse_resp(resp)
            assert "@context" in js
            resp = self.client.get("%s&%s=1" % (i, j))
            js = parse_resp(resp)
            assert "@context" not in js
            resp = self.client.get("%s&%s=true" % (i, j))
            js = parse_resp(resp)
            assert "@context" not in js

    def test_detail(self):
        """ Show only one plugin"""
        resp = self.client.get("/api/plugins/dummy/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "endpoint:plugins/dummy_0.1"

    def test_default(self):
        """ Show only one plugin"""
        resp = self.client.get("/api/plugins/default/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "endpoint:plugins/dummy_0.1"

    def test_context(self):
        resp = self.client.get("/api/contexts/context.jsonld")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert "@context" in js
        assert check_dict(
            js["@context"],
            {"marl": "http://www.gsi.upm.es/ontologies/marl/ns#"})

    def test_schema(self):
        resp = self.client.get("/api/schemas/definitions.json")
        self.assertCode(resp, 200)
        assert "$schema" in resp.data.decode()

    def test_help(self):
        resp = self.client.get("/api/?help=true")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert "valid_parameters" in js
        assert "help" in js["valid_parameters"]

    def test_conversion(self):
        self.app.config['TESTING'] = False  # Errors are expected in this case
        resp = self.client.get("/api/?input=hello&algo=emotion-random&emotionModel=DOES NOT EXIST")
        self.assertCode(resp, 404)
