#!/bin/env python2
# -*- py-which-shell: "python2"; -*-
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


class ShelfTest(ShelfMixin, SenpyPlugin):

    def test(self, key=None, value=None):
        assert isinstance(self.sh, shelve.Shelf)
        assert key in self.sh
        print('Checking: sh[{}] == {}'.format(key, value))
        print('SH[{}]: {}'.format(key, self.sh[key]))
        assert self.sh[key] == value
        


class ModelsTest(TestCase):
    shelf_file = 'shelf_test.db'


    def tearDown(self):
        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)

    setUp = tearDown
        
    def test_shelf(self):
        ''' A shelf is created and the value is stored '''
        a = ShelfTest(info={'name': 'shelve',
                            'version': 'test',
                            'shelf_file': self.shelf_file})
        assert a.sh == {}
        assert a.shelf_file == self.shelf_file

        a.sh['a'] = 'fromA'

        a.test(key='a', value='fromA')
        del(a)
        assert os.path.isfile(self.shelf_file)
        sh = shelve.open(self.shelf_file)
        assert sh['a'] == 'fromA'


    def test_two(self):
        ''' Reusing the values of a previous shelf '''
        a = ShelfTest(info={'name': 'shelve',
                            'version': 'test',
                            'shelf_file': self.shelf_file})
        print('Shelf file: %s' % a.shelf_file)
        a.sh['a'] = 'fromA'
        a.close()

        b = ShelfTest(info={'name': 'shelve',
                            'version': 'test',
                            'shelf_file': self.shelf_file})
        b.test(key='a', value='fromA')
        b.sh['a'] = 'fromB'
        assert b.sh['a'] == 'fromB'
