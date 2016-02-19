#!/bin/env python

import os
import logging
import shelve
import shutil
import tempfile

import json
import os
from unittest import TestCase
from senpy.models import Results, Entry
from senpy.plugins import SenpyPlugin, ShelfMixin


class ShelfTest(ShelfMixin, SenpyPlugin):

    def test(self, key=None, value=None):
        assert isinstance(self.sh, shelve.Shelf)
        assert key in self.sh
        print('Checking: sh[{}] == {}'.format(key, value))
        print('SH[{}]: {}'.format(key, self.sh[key]))
        assert self.sh[key] == value
        


class ModelsTest(TestCase):


    def tearDown(self):
        if os.path.exists(self.shelf_dir):
            shutil.rmtree(self.shelf_dir)

        if os.path.isfile(self.shelf_file):
            os.remove(self.shelf_file)

    def setUp(self):
        self.shelf_dir = tempfile.mkdtemp()
        self.shelf_file = os.path.join(self.shelf_dir, "shelf")
        
    def test_shelf(self):
        ''' A shelf is created and the value is stored '''
        a = ShelfTest(info={'name': 'shelve',
                            'version': 'test',
                            'shelf_file': self.shelf_file})
        assert a.sh == {}
        assert a.shelf_file == self.shelf_file

        a.sh['a'] = 'fromA'
        a.test(key='a', value='fromA')

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
