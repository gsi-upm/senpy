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
        cls.app.debug = False
        cls.client = cls.app.test_client()
        cls.senpy = Senpy(default_plugins=True)
        cls.senpy.init_app(cls.app)
        cls.dir = os.path.join(os.path.dirname(__file__), "..")
        cls.senpy.add_folder(cls.dir)
        cls.senpy.activate_plugin("Dummy", sync=True)
        cls.senpy.activate_plugin("DummyRequired", sync=True)
        cls.senpy.default_plugin = 'Dummy'

    def assertCode(self, resp, code):
        self.assertEqual(resp.status_code, code)

    def test_playground(self):
        resp = self.client.get("/")
        assert "main.js" in resp.get_data(as_text=True)

    def test_home(self):
        """
        Calling with no arguments should ask the user for more arguments
        """
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
        resp = self.client.get("/api/?i=My aloha mohame&with_parameters=True")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert "@context" in js
        assert "entries" in js

    def test_analysis_extra(self):
        """
        Extra params that have a default should
        """
        resp = self.client.get("/api/?i=My aloha mohame&algo=Dummy&with_parameters=true")
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
        self.app.debug = False
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired")
        self.assertCode(resp, 400)
        js = parse_resp(resp)
        logging.debug("Got response: %s", js)
        assert isinstance(js, models.Error)
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired&example=notvalid")
        self.assertCode(resp, 400)
        resp = self.client.get("/api/?i=My aloha mohame&algo=DummyRequired&example=a")
        self.assertCode(resp, 200)

    def test_error(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        self.app.debug = False
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
        assert list(p for p in plugins if p['name'] == "Dummy")
        assert "@context" in js

    def test_headers(self):
        for i, j in product(["/api/plugins/?nothing=", "/api/?i=test&"],
                            ["inHeaders"]):
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
        resp = self.client.get("/api/plugins/Dummy/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "endpoint:plugins/Dummy_0.1"

    def test_default(self):
        """ Show only one plugin"""
        resp = self.client.get("/api/plugins/default/")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        logging.debug(js)
        assert "@id" in js
        assert js["@id"] == "endpoint:plugins/Dummy_0.1"

    def test_context(self):
        resp = self.client.get("/api/contexts/context.jsonld")
        self.assertCode(resp, 200)
        js = parse_resp(resp)
        assert "@context" in js
        assert check_dict(
            js["@context"],
            {"marl": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"})

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
        resp = self.client.get("/api/?input=hello&algo=emoRand&emotionModel=DOES NOT EXIST")
        self.assertCode(resp, 404)
