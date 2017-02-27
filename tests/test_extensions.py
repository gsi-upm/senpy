from __future__ import print_function
import os
import logging

try:
    from unittest import mock
except ImportError:
    import mock

from functools import partial
from senpy.extensions import Senpy
from senpy.models import Error
from flask import Flask
from unittest import TestCase


class ExtensionsTest(TestCase):
    def setUp(self):
        self.app = Flask('test_extensions')
        self.dir = os.path.join(os.path.dirname(__file__))
        self.senpy = Senpy(plugin_folder=self.dir,
                           app=self.app,
                           default_plugins=False)
        self.senpy.activate_plugin("Dummy", sync=True)

    def test_init(self):
        """ Initialising the app with the extension.  """
        assert hasattr(self.app, "senpy")
        tapp = Flask("temp app")
        self.senpy.init_app(tapp)
        assert hasattr(tapp, "senpy")

    def test_discovery(self):
        """ Discovery of plugins in given folders.  """
        # noinspection PyProtectedMember
        assert self.dir in self.senpy._search_folders
        print(self.senpy.plugins)
        assert "Dummy" in self.senpy.plugins

    def test_enabling(self):
        """ Enabling a plugin """
        info = {
            'name': 'TestPip',
            'module': 'dummy',
            'requirements': ['noop'],
            'version': 0
        }
        root = os.path.join(self.dir, 'plugins', 'dummy_plugin')
        name, module = self.senpy._load_plugin_from_info(info, root=root)
        assert name == 'TestPip'
        assert module
        import noop
        dir(noop)

    def test_installing(self):
        """ Enabling a plugin """
        self.senpy.activate_all(sync=True)
        assert len(self.senpy.plugins) >= 3
        assert self.senpy.plugins["Sleep"].is_activated

    def test_disabling(self):
        """ Disabling a plugin """
        self.senpy.deactivate_all(sync=True)
        assert not self.senpy.plugins["Dummy"].is_activated
        assert not self.senpy.plugins["Sleep"].is_activated

    def test_default(self):
        """ Default plugin should be set """
        assert self.senpy.default_plugin
        assert self.senpy.default_plugin.name == "Dummy"
        self.senpy.deactivate_all(sync=True)
        logging.debug("Default: {}".format(self.senpy.default_plugin))
        assert self.senpy.default_plugin is None

    def test_noplugin(self):
        """ Don't analyse if there isn't any plugin installed """
        self.senpy.deactivate_all(sync=True)
        self.assertRaises(Error, partial(self.senpy.analyse, input="tupni"))
        self.assertRaises(Error,
                          partial(
                              self.senpy.analyse,
                              input="tupni",
                              algorithm='Dummy'))

    def test_analyse(self):
        """ Using a plugin """
        # I was using mock until plugin started inheriting
        # Leaf (defaultdict with  __setattr__ and __getattr__.
        r1 = self.senpy.analyse(
            algorithm="Dummy", input="tupni", output="tuptuo")
        r2 = self.senpy.analyse(input="tupni", output="tuptuo")
        assert r1.analysis[0] == "plugins/Dummy_0.1"
        assert r2.analysis[0] == "plugins/Dummy_0.1"
        assert r1.entries[0].text == 'input'

    def test_analyse_error(self):
        mm = mock.MagicMock()
        mm.analyse_entry.side_effect = Error('error on analysis', status=900)
        self.senpy.plugins['MOCK'] = mm
        resp = self.senpy.analyse(input='nothing', algorithm='MOCK')
        assert resp['message'] == 'error on analysis'
        assert resp['status'] == 900
        mm.analyse.side_effect = Exception('generic exception on analysis')
        mm.analyse_entry.side_effect = Exception(
            'generic exception on analysis')
        resp = self.senpy.analyse(input='nothing', algorithm='MOCK')
        assert resp['message'] == 'generic exception on analysis'
        assert resp['status'] == 500

    def test_filtering(self):
        """ Filtering plugins """
        assert len(self.senpy.filter_plugins(name="Dummy")) > 0
        assert not len(self.senpy.filter_plugins(name="notdummy"))
        assert self.senpy.filter_plugins(name="Dummy", is_activated=True)
        self.senpy.deactivate_plugin("Dummy", sync=True)
        assert not len(
            self.senpy.filter_plugins(name="Dummy", is_activated=True))

    def test_load_default_plugins(self):
        senpy = Senpy(plugin_folder=self.dir, default_plugins=True)
        assert len(senpy.plugins) > 1
