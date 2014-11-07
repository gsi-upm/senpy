import os
import logging
try:
    import unittest.mock as mock
except ImportError:
    import mock
from senpy.extensions import Senpy
from flask import Flask
from flask.ext.testing import TestCase


class Extensions_Test(TestCase):
    def create_app(self):
        self.app = Flask("test_extensions")
        self.senpy = Senpy()
        self.senpy.init_app(self.app)
        self.dir = os.path.join(os.path.dirname(__file__), "..")
        self.senpy.add_folder(self.dir)
        return self.app

    def test_init(self):
        """ Initialising the app with the extension.  """
        assert hasattr(self.app, "senpy")
        tapp = Flask("temp app")
        tsen = Senpy(tapp)
        assert hasattr(tapp, "senpy")

    def test_discovery(self):
        """ Discovery of plugins in given folders.  """
        assert self.dir in self.senpy._search_folders
        print self.senpy.plugins
        assert "dummy" in self.senpy.plugins


    def test_enabling(self):
        """ Enabling a plugin """
        self.senpy.enable_plugin("dummy")
        assert self.senpy.plugins["dummy"].enabled

    def test_disabling(self):
        """ Disabling a plugin """
        self.senpy.enable_plugin("dummy")
        self.senpy.disable_plugin("dummy")
        assert self.senpy.plugins["dummy"].enabled == False

    def test_default(self):
        """ Default plugin should be set """
        assert self.senpy.default_plugin
        assert self.senpy.default_plugin == "dummy"

    def test_analyse(self):
        """ Using a plugin """
        with mock.patch.object(self.senpy.plugins["dummy"], "analyse") as mocked:
            self.senpy.analyse(algorithm="dummy", input="tupni", output="tuptuo")
            self.senpy.analyse(input="tupni", output="tuptuo")
        mocked.assert_any_call(input="tupni", output="tuptuo", algorithm="dummy")
        mocked.assert_any_call(input="tupni", output="tuptuo")
        for plug in self.senpy.plugins:
            self.senpy.disable_plugin(plug)
        resp = self.senpy.analyse(input="tupni")
        logging.debug("Response: {}".format(resp))
        assert resp["status"] == 400

    def test_filtering(self):
        """ Filtering plugins """
        assert len(self.senpy.filter_plugins(name="dummy"))>0
        assert not len(self.senpy.filter_plugins(name="notdummy"))
        assert self.senpy.filter_plugins(name="dummy", enabled=True)
        self.senpy.disable_plugin("dummy")
        assert not len(self.senpy.filter_plugins(name="dummy", enabled=True))
