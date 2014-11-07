import os
import logging
try:
    import unittest.mock as mock
except ImportError:
    import mock
from senpy.extensions import Senpy
from flask import Flask
from flask.ext.testing import TestCase

def check_dict(indic, template):
        return all(item in indic.items() for item in template.items())

class Blueprints_Test(TestCase):
    def create_app(self):
        self.app = Flask("test_extensions")
        self.senpy = Senpy()
        self.senpy.init_app(self.app)
        self.dir = os.path.join(os.path.dirname(__file__), "..")
        self.senpy.add_folder(self.dir)
        return self.app


    def test_home(self):
        """ Calling with no arguments should ask the user for more arguments """
        resp = self.client.get("/")
        self.assert200(resp)
        logging.debug(resp.json)
        assert resp.json["status"] == "failed"
        atleast = {
            "status": "failed",
            "message": "Missing or invalid parameters",
        }
        assert check_dict(resp.json, atleast)

