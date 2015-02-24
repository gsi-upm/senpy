import os
import logging

try:
    import unittest.mock as mock
except ImportError:
    import mock
from senpy.extensions import Senpy
from flask import Flask
from flask.ext.testing import TestCase
from gevent import sleep
from itertools import product


def check_dict(indic, template):
    return all(item in indic.items() for item in template.items())


class BlueprintsTest(TestCase):

    def create_app(self):
        self.app = Flask("test_extensions")
        self.senpy = Senpy()
        self.senpy.init_app(self.app)
        self.dir = os.path.join(os.path.dirname(__file__), "..")
        self.senpy.add_folder(self.dir)
        self.senpy.activate_plugin("Dummy", sync=True)
        return self.app

    def test_home(self):
        """
        Calling with no arguments should ask the user for more arguments
        """
        resp = self.client.get("/")
        self.assert404(resp)
        logging.debug(resp.json)
        assert resp.json["status"] == 404
        atleast = {
            "status": 404,
            "message": "Missing or invalid parameters",
        }
        assert check_dict(resp.json, atleast)

    def test_analysis(self):
        """
        The dummy plugin returns an empty response,\
        it should contain the context
        """
        resp = self.client.get("/?i=My aloha mohame")
        self.assert200(resp)
        logging.debug("Got response: %s", resp.json)
        assert "@context" in resp.json
        assert check_dict(
            resp.json["@context"],
            {"marl": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"})
        assert "entries" in resp.json

    def test_list(self):
        """ List the plugins """
        resp = self.client.get("/plugins/")
        self.assert200(resp)
        logging.debug(resp.json)
        assert "Dummy" in resp.json
        assert "@context" in resp.json

    def test_headers(self):
        for i, j in product(["/plugins/?nothing=", "/?i=test&"],
                            ["headers", "inHeaders"]):
            resp = self.client.get("%s" % (i))
            assert "@context" in resp.json
            resp = self.client.get("%s&%s=0" % (i, j))
            assert "@context" in resp.json
            resp = self.client.get("%s&%s=1" % (i, j))
            assert "@context" not in resp.json
            resp = self.client.get("%s&%s=true" % (i, j))
            assert "@context" not in resp.json

    def test_detail(self):
        """ Show only one plugin"""
        resp = self.client.get("/plugins/Dummy")
        self.assert200(resp)
        logging.debug(resp.json)
        assert "@id" in resp.json
        assert resp.json["@id"] == "Dummy_0.1"

    def test_activate(self):
        """ Activate and deactivate one plugin """
        resp = self.client.get("/plugins/Dummy/deactivate")
        self.assert200(resp)
        sleep(0.5)
        resp = self.client.get("/plugins/Dummy")
        self.assert200(resp)
        assert "is_activated" in resp.json
        assert resp.json["is_activated"] == False
        resp = self.client.get("/plugins/Dummy/activate")
        self.assert200(resp)
        sleep(0.5)
        resp = self.client.get("/plugins/Dummy")
        self.assert200(resp)
        assert "is_activated" in resp.json
        assert resp.json["is_activated"] == True

    def test_default(self):
        """ Show only one plugin"""
        resp = self.client.get("/default")
        self.assert200(resp)
        logging.debug(resp.json)
        assert "@id" in resp.json
        assert resp.json["@id"] == "Dummy_0.1"
        resp = self.client.get("/plugins/Dummy/deactivate")
        self.assert200(resp)
        sleep(0.5)
        resp = self.client.get("/default")
        self.assert404(resp)
