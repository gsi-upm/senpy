#!/bin/env python

import os
import sys
import pickle
import shutil
import tempfile

from unittest import TestCase
from senpy.models import Results, Entry, EmotionSet, Emotion, Plugins
from senpy import plugins
from senpy.plugins.conversion.emotion.centroids import CentroidConversion

import pandas as pd


class ShelfDummyPlugin(plugins.SentimentPlugin, plugins.ShelfMixin):
    '''Dummy plugin for tests.'''
    name = 'Shelf'
    version = 0
    author = 'the senpy community'

    def activate(self, *args, **kwargs):
        if 'counter' not in self.sh:
            self.sh['counter'] = 0
        self.save()

    def deactivate(self, *args, **kwargs):
        self.save()

    def analyse(self, *args, **kwargs):
        self.sh['counter'] = self.sh['counter'] + 1
        e = Entry()
        e.nif__isString = self.sh['counter']
        r = Results()
        r.entries.append(e)
        return r


class PluginsTest(TestCase):
    def tearDown(self):
        if os.path.exists(self.shelf_dir):
            shutil.rmtree(self.shelf_dir)
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)

    def setUp(self):
        self.shelf_dir = tempfile.mkdtemp()
        self.shelf_file = os.path.join(self.shelf_dir, "shelf")

    def test_serialize(self):
        '''A plugin should be serializable and de-serializable'''
        dummy = ShelfDummyPlugin()
        dummy.serialize()

    def test_jsonld(self):
        '''A plugin should be serializable and de-serializable'''
        dummy = ShelfDummyPlugin()
        dummy.jsonld()

    def test_shelf_file(self):
        a = ShelfDummyPlugin(
            info={'name': 'default_shelve_file',
                  'description': 'Dummy plugin for tests',
                  'version': 'test'})
        a.activate()
        assert os.path.isfile(a.shelf_file)
        os.remove(a.shelf_file)

    def test_plugin_filter(self):
        ps = Plugins()
        for i in (plugins.SentimentPlugin,
                  plugins.EmotionPlugin,
                  plugins.AnalysisPlugin):
            p = i(name='Plugin_{}'.format(i.__name__),
                  description='TEST',
                  version=0,
                  author='NOBODY')
            ps.plugins.append(p)
        assert len(ps.plugins) == 3
        cases = [('AnalysisPlugin', 3),
                 ('SentimentPlugin', 1),
                 ('EmotionPlugin', 1)]

        for name, num in cases:
            res = list(plugins.pfilter(ps.plugins, plugin_type=name))
            assert len(res) == num

    def test_shelf(self):
        ''' A shelf is created and the value is stored '''
        newfile = self.shelf_file + "new"
        a = ShelfDummyPlugin(info={
            'name': 'shelve',
            'description': 'Shelf plugin for tests',
            'version': 'test',
            'shelf_file': newfile
        })
        assert a.sh == {}
        a.activate()
        assert a.sh == {'counter': 0}
        assert a.shelf_file == newfile

        a.sh['a'] = 'fromA'
        assert a.sh['a'] == 'fromA'

        a.save()

        sh = pickle.load(open(newfile, 'rb'))

        assert sh['a'] == 'fromA'

    def test_dummy_shelf(self):
        with open(self.shelf_file, 'wb') as f:
            pickle.dump({'counter': 99}, f)
        a = ShelfDummyPlugin(info={
            'name': 'DummyShelf',
            'description': 'Dummy plugin for tests',
            'shelf_file': self.shelf_file,
            'version': 'test'
        })
        a.activate()

        assert a.shelf_file == self.shelf_file
        res1 = a.analyse(input=1)
        assert res1.entries[0].nif__isString == 100
        a.deactivate()
        del a

        with open(self.shelf_file, 'rb') as f:
            sh = pickle.load(f)
            assert sh['counter'] == 100

    def test_corrupt_shelf(self):
        ''' Reusing the values of a previous shelf '''

        emptyfile = os.path.join(self.shelf_dir, "emptyfile")
        invalidfile = os.path.join(self.shelf_dir, "invalid_file")
        with open(emptyfile, 'w+b'), open(invalidfile, 'w+b') as inf:
            inf.write(b'ohno')

        files = {emptyfile: ['empty file', (EOFError, IndexError)],
                 invalidfile: ['invalid file', (pickle.UnpicklingError, IndexError)]}

        for fn in files:
            with open(fn, 'rb') as f:
                msg, error = files[fn]
                a = ShelfDummyPlugin(info={
                    'name': 'test_corrupt_shelf_{}'.format(msg),
                    'description': 'Dummy plugin for tests',
                    'version': 'test',
                    'shelf_file': f.name
                })
                assert os.path.isfile(a.shelf_file)
                print('Shelf file: %s' % a.shelf_file)
                with self.assertRaises(error):
                    a.sh['a'] = 'fromA'
                    a.save()
                del a._sh
                assert os.path.isfile(a.shelf_file)
                a.force_shelf = True
                a.sh['a'] = 'fromA'
                a.save()
                b = pickle.load(f)
                assert b['a'] == 'fromA'

    def test_reuse_shelf(self):
        ''' Reusing the values of a previous shelf '''
        a = ShelfDummyPlugin(info={
            'name': 'shelve',
            'description': 'Dummy plugin for tests',
            'version': 'test',
            'shelf_file': self.shelf_file
        })
        a.activate()
        print('Shelf file: %s' % a.shelf_file)
        a.sh['a'] = 'fromA'
        a.save()

        b = ShelfDummyPlugin(info={
            'name': 'shelve',
            'description': 'Dummy plugin for tests',
            'version': 'test',
            'shelf_file': self.shelf_file
        })
        b.activate()
        assert b.sh['a'] == 'fromA'
        b.sh['a'] = 'fromB'
        assert b.sh['a'] == 'fromB'

    def test_extra_params(self):
        ''' Should be able to set extra parameters'''
        a = ShelfDummyPlugin(info={
            'name': 'shelve',
            'description': 'Dummy shelf plugin for tests',
            'version': 'test',
            'shelf_file': self.shelf_file,
            'extra_params': {
                'example': {
                    'aliases': ['example', 'ex'],
                    'required': True,
                    'default': 'nonsense'
                }
            }
        })
        assert 'example' in a.extra_params

    def test_box(self):

        class MyBox(plugins.Box):
            ''' Vague description'''

            author = 'me'
            version = 0

            def input(self, entry, **kwargs):
                return entry.text

            def predict_one(self, input):
                return 'SIGN' in input

            def output(self, output, entry, **kwargs):
                if output:
                    entry.myAnnotation = 'DETECTED'
                return entry

            test_cases = [
                {
                    'input': "nothing here",
                    'expected': {'myAnnotation': 'DETECTED'},
                    'should_fail': True
                }, {
                    'input': "SIGN",
                    'expected': {'myAnnotation': 'DETECTED'}
                }]

        MyBox().test()

    def test_sentimentbox(self):

        class SentimentBox(plugins.MappingMixin, plugins.SentimentBox):
            ''' Vague description'''

            author = 'me'
            version = 0

            mappings = {'happy': 'marl:Positive', 'sad': 'marl:Negative'}

            def predict_one(self, input, **kwargs):
                return 'happy' if ':)' in input else 'sad'

            test_cases = [
                {
                    'input': 'a happy face :)',
                    'polarity': 'marl:Positive'
                }, {
                    'input': "Nothing",
                    'polarity': 'marl:Negative'
                }]

        SentimentBox().test()

    def test_conversion_centroids(self):
        info = {
            "name": "CentroidTest",
            "description": "Centroid test",
            "version": 0,
            "centroids": {
                "c1": {"V1": 0.5,
                       "V2": 0.5},
                "c2": {"V1": -0.5,
                       "V2": 0.5},
                "c3": {"V1": -0.5,
                       "V2": -0.5},
                "c4": {"V1": 0.5,
                       "V2": -0.5}},
            "aliases": {
                "V1": "X-dimension",
                "V2": "Y-dimension"
            },
            "centroids_direction": ["emoml:big6", "emoml:fsre-dimensions"]
        }
        c = CentroidConversion(info)
        print(c.serialize())

        es1 = EmotionSet()
        e1 = Emotion()
        e1.onyx__hasEmotionCategory = "c1"
        es1.onyx__hasEmotion.append(e1)
        res = c._forward_conversion(es1)
        assert res["X-dimension"] == 0.5
        assert res["Y-dimension"] == 0.5
        print(res)

        e2 = Emotion()
        e2.onyx__hasEmotionCategory = "c2"
        es1.onyx__hasEmotion.append(e2)
        res = c._forward_conversion(es1)
        assert res["X-dimension"] == 0
        assert res["Y-dimension"] == 1
        print(res)

        e = Emotion()
        e["X-dimension"] = -0.2
        e["Y-dimension"] = -0.3
        res = c._backwards_conversion(e)
        assert res["onyx:hasEmotionCategory"] == "c3"
        print(res)

        e = Emotion()
        e["X-dimension"] = -0.2
        e["Y-dimension"] = 0.3
        res = c._backwards_conversion(e)
        assert res["onyx:hasEmotionCategory"] == "c2"

    def _test_evaluation(self):
        testdata = []
        for i in range(50):
            testdata.append(["good", 1])
        for i in range(50):
            testdata.append(["bad", 0])
        dataset = pd.DataFrame(testdata, columns=['text', 'polarity'])

        class DummyPlugin(plugins.TextBox):
            description = 'Plugin to test evaluation'
            version = 0

            def predict_one(self, input):
                return 0

        class SmartPlugin(plugins.TextBox):
            description = 'Plugin to test evaluation'
            version = 0

            def predict_one(self, input):
                if input == 'good':
                    return 1
                return 0

        dpipe = DummyPlugin()
        results = plugins.evaluate(datasets={'testdata': dataset}, plugins=[dpipe], flatten=True)
        dumb_metrics = results[0].metrics[0]
        assert abs(dumb_metrics['accuracy'] - 0.5) < 0.01

        spipe = SmartPlugin()
        results = plugins.evaluate(datasets={'testdata': dataset}, plugins=[spipe], flatten=True)
        smart_metrics = results[0].metrics[0]
        assert abs(smart_metrics['accuracy'] - 1) < 0.01

    def test_evaluation(self):
        if sys.version_info < (3, 0):
            with self.assertRaises(Exception) as context:
                self._test_evaluation()
            self.assertTrue('GSITK ' in str(context.exception))
        else:
            self._test_evaluation()


def make_mini_test(fpath):
    def mini_test(self):
        for plugin in plugins.from_path(fpath, install=True):
            plugin.test()
    return mini_test


def _add_tests():
    root = os.path.join(os.path.dirname(__file__), '..')
    print(root)
    for fpath in plugins.find_plugins([root, ]):
        pass
        t_method = make_mini_test(fpath)
        t_method.__name__ = 'test_plugin_{}'.format(fpath)
        setattr(PluginsTest, t_method.__name__, t_method)
        del t_method


_add_tests()
