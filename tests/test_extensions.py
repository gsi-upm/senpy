from __future__ import print_function
import os
from copy import deepcopy
import logging


from functools import partial
from senpy.extensions import Senpy
from senpy import plugins
from senpy.models import Error, Results, Entry, EmotionSet, Emotion, Plugin
from senpy import api
from flask import Flask
from unittest import TestCase


def analyse(instance, **kwargs):
    basic = api.parse_params(kwargs, api.API_PARAMS)
    request = api.parse_call(basic)
    return instance.analyse(request)


class ExtensionsTest(TestCase):
    def setUp(self):
        self.app = Flask('test_extensions')
        self.examples_dir = os.path.join(os.path.dirname(__file__), '..', 'example-plugins')
        self.senpy = Senpy(plugin_folder=self.examples_dir,
                           app=self.app,
                           default_plugins=False)
        self.senpy.deactivate_all()
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
        print(self.senpy.plugins())
        assert self.senpy.get_plugin("dummy")

    def test_add_delete(self):
        '''Should be able to add and delete new plugins. '''
        new = plugins.Analysis(name='new', description='new', version=0)
        self.senpy.add_plugin(new)
        assert new in self.senpy.plugins(is_activated=False)
        self.senpy.delete_plugin(new)
        assert new not in self.senpy.plugins(is_activated=False)

    def test_adding_folder(self):
        """ It should be possible for senpy to look for plugins in more folders. """
        senpy = Senpy(plugin_folder=None,
                      app=self.app,
                      default_plugins=False)
        assert not senpy.analysis_plugins
        senpy.add_folder(self.examples_dir)
        assert senpy.plugins(plugin_type=plugins.AnalysisPlugin, is_activated=False)
        self.assertRaises(AttributeError, senpy.add_folder, 'DOES NOT EXIST')

    def test_installing(self):
        """ Installing a plugin """
        info = {
            'name': 'TestPip',
            'module': 'mynoop',
            'description': None,
            'requirements': ['noop'],
            'version': 0
        }
        module = plugins.from_info(info, root=self.examples_dir, install=True)
        assert module.name == 'TestPip'
        assert module
        import noop
        dir(noop)

    def test_enabling(self):
        """ Enabling a plugin """
        self.senpy.activate_all(sync=True)
        assert len(self.senpy.plugins()) >= 3
        assert self.senpy.get_plugin("Sleep").is_activated

    def test_installing_nonexistent(self):
        """ Fail if the dependencies cannot be met """
        info = {
            'name': 'TestPipFail',
            'module': 'dummy',
            'description': None,
            'requirements': ['IAmMakingThisPackageNameUpToFail'],
            'version': 0
        }
        with self.assertRaises(Error):
            plugins.install_deps(info)

    def test_disabling(self):
        """ Disabling a plugin """
        self.senpy.deactivate_all(sync=True)
        assert not self.senpy.get_plugin("dummy").is_activated
        assert not self.senpy.get_plugin("sleep").is_activated

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
        self.assertRaises(Error, partial(analyse, self.senpy, input="tupni"))

    def test_analyse(self):
        """ Using a plugin """
        # I was using mock until plugin started inheriting
        # Leaf (defaultdict with  __setattr__ and __getattr__.
        r1 = analyse(self.senpy, algorithm="Dummy", input="tupni", output="tuptuo")
        r2 = analyse(self.senpy, input="tupni", output="tuptuo")
        assert r1.analysis[0].algorithm == "endpoint:plugins/Dummy_0.1"
        assert r2.analysis[0].algorithm == "endpoint:plugins/Dummy_0.1"
        assert r1.entries[0]['nif:isString'] == 'input'

    def test_analyse_empty(self):
        """ Trying to analyse when no plugins are installed should raise an error."""
        senpy = Senpy(plugin_folder=None,
                      app=self.app,
                      default_plugins=False)
        self.assertRaises(Error, senpy.analyse, Results(), [])

    def test_analyse_wrong(self):
        """ Trying to analyse with a non-existent plugin should raise an error."""
        self.assertRaises(Error, analyse, self.senpy, algorithm='DOES NOT EXIST', input='test')

    def test_analyse_jsonld(self):
        """ Using a plugin with JSON-LD input"""
        js_input = '''{
        "@id": "prueba",
        "@type": "results",
        "entries": [
          {"@id": "entry1",
           "nif:isString": "tupni",
           "@type": "entry"
          }
        ]
        }'''
        r1 = analyse(self.senpy,
                     algorithm="Dummy",
                     input=js_input,
                     informat="json-ld",
                     output="tuptuo")
        r2 = analyse(self.senpy,
                     input="tupni",
                     output="tuptuo")
        assert r1.analysis[0].algorithm == "endpoint:plugins/Dummy_0.1"
        assert r2.analysis[0].algorithm == "endpoint:plugins/Dummy_0.1"
        assert r1.entries[0]['nif:isString'] == 'input'

    def test_analyse_error(self):
        class ErrorPlugin(plugins.Analysis):
            author = 'nobody'
            version = 0
            ex = Error()

            def process(self, *args, **kwargs):
                raise self.ex

        m = ErrorPlugin(ex=Error('error in analysis', status=500))
        self.senpy.add_plugin(m)
        try:
            analyse(self.senpy, input='nothing', algorithm='ErrorPlugin')
            assert False
        except Error as ex:
            assert 'error in analysis' in ex['message']
            assert ex['status'] == 500

        m.ex = Exception('generic exception on analysis')

        try:
            analyse(self.senpy, input='nothing', algorithm='ErrorPlugin')
            assert False
        except Exception as ex:
            assert 'generic exception on analysis' in str(ex)

    def test_filtering(self):
        """ Filtering plugins """
        assert len(self.senpy.plugins(name="Dummy")) > 0
        assert not len(self.senpy.plugins(name="NotDummy"))
        assert self.senpy.plugins(name="Dummy", is_activated=True)
        self.senpy.deactivate_plugin("Dummy", sync=True)
        assert not len(self.senpy.plugins(name="Dummy",
                                          is_activated=True))

    def test_load_default_plugins(self):
        senpy = Senpy(plugin_folder=self.examples_dir, default_plugins=True)
        assert len(senpy.plugins(is_activated=False)) > 1

    def test_convert_emotions(self):
        self.senpy.activate_all(sync=True)
        plugin = Plugin({
            'id': 'imaginary',
            'onyx:usesEmotionModel': 'emoml:fsre-dimensions'
        })
        eSet1 = EmotionSet()
        eSet1.prov__wasGeneratedBy = plugin['@id']
        eSet1['onyx:hasEmotion'].append(Emotion({
            'emoml:arousal': 1,
            'emoml:potency': 0,
            'emoml:valence': 0
        }))
        response = Results({
            'analysis': [plugin],
            'entries': [Entry({
                'nif:isString': 'much ado about nothing',
                'emotions': [eSet1]
            })]
        })
        params = {'emotionModel': 'emoml:big6',
                  'algorithm': ['conversion'],
                  'conversion': 'full'}
        r1 = deepcopy(response)
        r1.parameters = params
        self.senpy.analyse(r1)
        assert len(r1.entries[0].emotions) == 2
        params['conversion'] = 'nested'
        r2 = deepcopy(response)
        r2.parameters = params
        self.senpy.analyse(r2)
        assert len(r2.entries[0].emotions) == 1
        assert r2.entries[0].emotions[0]['prov:wasDerivedFrom'] == eSet1
        params['conversion'] = 'filtered'
        r3 = deepcopy(response)
        r3.parameters = params
        self.senpy.analyse(r3)
        assert len(r3.entries[0].emotions) == 1
        r3.jsonld()
