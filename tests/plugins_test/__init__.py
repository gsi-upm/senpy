import os
import logging
import shelve

try:
    import unittest.mock as mock
except ImportError:
    import mock
import json
import os
from unittest import TestCase
from senpy.models import Response, Entry
from senpy.plugins import SenpyPlugin, ShelfMixin


class ModelsTest(TestCase):

    # def test_shelf(self):
    #     class ShelfTest(ShelfMixin):
    #         pass
    #     a = ShelfTest()
    #     print(type(a.sh))
    #     assert(False)
        
    def test_shelf(self):
        class ShelfTest(ShelfMixin, SenpyPlugin):
            pass
        a = ShelfTest({'name': 'shelve', 'version': 'test'})
        print(type(a.sh))
        a.context = "ohno"
        del a.context
        print(a)
        a.sh['classifier'] = {'name': 'ohno'}
        assert a.name == 'shelve'
        assert isinstance(a.sh, shelve.Shelf)
        a.close()
        b = ShelfTest({'name': 'shelve', 'version': 'test'})
        assert b.name == 'shelve'
        assert b.sh['classifier']
        assert b.sh['classifier']['name'] == 'ohno'
        assert isinstance(b.sh, shelve.Shelf)
