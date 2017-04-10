from __future__ import print_function
import os
from copy import deepcopy
import logging

try:
    from unittest import mock
except ImportError:
    import mock

from functools import partial
from senpy.extensions import Senpy
from senpy.models import Error, Results, Entry, EmotionSet, Emotion, Plugin
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
            'description': None,
            'requirements': ['noop'],
            'version': 0
        }
        root = os.path.join(self.dir, 'plugins', 'dummy_plugin')
        name, module = self.senpy._load_plugin_from_info(info, root=root)
        assert name == 'TestPip'
        assert module
        import noop
        dir(noop)
        self.senpy.install_deps()

    def test_installing(self):
        """ Enabling a plugin """
        self.senpy.activate_all(sync=True)
        assert len(self.senpy.plugins) >= 3
        assert self.senpy.plugins["Sleep"].is_activated

    def test_installing_nonexistent(self):
        """ Fail if the dependencies cannot be met """
        info = {
            'name': 'TestPipFail',
            'module': 'dummy',
            'description': None,
            'requirements': ['IAmMakingThisPackageNameUpToFail'],
            'version': 0
        }
        root = os.path.join(self.dir, 'plugins', 'dummy_plugin')
        with self.assertRaises(Error):
            name, module = self.senpy._load_plugin_from_info(info, root=root)

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

    def test_analyse_jsonld(self):
        """ Using a plugin with JSON-LD input"""
        js_input = '''{
        "@id": "prueba",
        "@type": "results",
        "entries": [
          {"@id": "entry1",
           "text": "tupni",
           "@type": "entry"
          }
        ]
        }'''
        r1 = self.senpy.analyse(algorithm="Dummy",
                                input=js_input,
                                informat="json-ld",
                                output="tuptuo")
        r2 = self.senpy.analyse(input="tupni", output="tuptuo")
        assert r1.analysis[0] == "plugins/Dummy_0.1"
        assert r2.analysis[0] == "plugins/Dummy_0.1"
        assert r1.entries[0].text == 'input'

    def test_analyse_error(self):
        mm = mock.MagicMock()
        mm.id = 'magic_mock'
        mm.analyse_entries.side_effect = Error('error on analysis', status=500)
        self.senpy.plugins['MOCK'] = mm
        try:
            self.senpy.analyse(input='nothing', algorithm='MOCK')
            assert False
        except Error as ex:
            assert ex['message'] == 'error on analysis'
            assert ex['status'] == 500

        mm.analyse.side_effect = Exception('generic exception on analysis')
        mm.analyse_entries.side_effect = Exception(
            'generic exception on analysis')

        try:
            self.senpy.analyse(input='nothing', algorithm='MOCK')
            assert False
        except Error as ex:
            assert ex['message'] == 'generic exception on analysis'
            assert ex['status'] == 500

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

    def test_convert_emotions(self):
        self.senpy.activate_all(sync=True)
        plugin = Plugin({
            'id': 'imaginary',
            'onyx:usesEmotionModel': 'emoml:fsre-dimensions'
        })
        eSet1 = EmotionSet()
        eSet1.prov__wasGeneratedBy = plugin['id']
        eSet1['onyx:hasEmotion'].append(Emotion({
            'emoml:arousal': 1,
            'emoml:potency': 0,
            'emoml:valence': 0
        }))
        response = Results({
            'entries': [Entry({
                'text': 'much ado about nothing',
                'emotions': [eSet1]
            })]
        })
        params = {'emotionModel': 'emoml:big6',
                  'conversion': 'full'}
        r1 = deepcopy(response)
        self.senpy.convert_emotions(r1,
                                    [plugin, ],
                                    params)
        assert len(r1.entries[0].emotions) == 2
        params['conversion'] = 'nested'
        r2 = deepcopy(response)
        self.senpy.convert_emotions(r2,
                                    [plugin, ],
                                    params)
        assert len(r2.entries[0].emotions) == 1
        assert r2.entries[0].emotions[0]['prov:wasDerivedFrom'] == eSet1
        params['conversion'] = 'filtered'
        r3 = deepcopy(response)
        self.senpy.convert_emotions(r3,
                                    [plugin, ],
                                    params)
        assert len(r3.entries[0].emotions) == 1

    # def test_async_plugin(self):
    #     """ We should accept multiprocessing plugins with async=False"""
    #     thread1 = self.senpy.activate_plugin("Async", sync=False)
    #     thread1.join(timeout=1)
    #     assert len(self.senpy.plugins['Async'].value) == 4

    #     resp = self.senpy.analyse(input='nothing', algorithm='Async')

    #     assert len(resp.entries[0].async_values) == 2
    #     self.senpy.activate_plugin("Async", sync=True)
