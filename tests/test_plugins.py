#!/bin/env python

import os
import pickle
import shutil
import tempfile

from unittest import TestCase
from senpy.models import Results, Entry, EmotionSet, Emotion
from senpy import plugins
from senpy.plugins.conversion.emotion.centroids import CentroidConversion


class ShelfDummyPlugin(plugins.SentimentPlugin, plugins.ShelfMixin):
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

    def test_shelf_file(self):
        a = ShelfDummyPlugin(
            info={'name': 'default_shelve_file',
                  'version': 'test'})
        a.activate()
        assert os.path.isfile(a.shelf_file)
        os.remove(a.shelf_file)

    def test_shelf(self):
        ''' A shelf is created and the value is stored '''
        newfile = self.shelf_file + "new"
        a = ShelfDummyPlugin(info={
            'name': 'shelve',
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
                    'name': 'shelve',
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
            'version': 'test',
            'shelf_file': self.shelf_file
        })
        a.activate()
        print('Shelf file: %s' % a.shelf_file)
        a.sh['a'] = 'fromA'
        a.save()

        b = ShelfDummyPlugin(info={
            'name': 'shelve',
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


def make_mini_test(plugin):
    def mini_test(self):
        plugin.test()
    return mini_test


def add_tests():
    root = os.path.dirname(__file__)
    plugs = plugins.load_plugins(os.path.join(root, ".."))
    for k, v in plugs.items():
        t_method = make_mini_test(v)
        t_method.__name__ = 'test_plugin_{}'.format(k)
        setattr(PluginsTest, t_method.__name__, t_method)
        del t_method


add_tests()
