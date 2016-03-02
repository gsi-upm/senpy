import os
import logging
from functools import partial

logger = logging.getLogger(__name__)

from unittest import TestCase
from senpy.cli import main_function
from senpy.models import Error


class CLITest(TestCase):

    def test_basic(self):
        self.assertRaises(Error, partial(main_function, []))
        res = main_function(['--input', 'test'])
        assert 'entries' in res
        res = main_function(['--input', 'test', '--algo', 'rand'])
        assert 'entries' in res
        assert 'analysis' in res
        assert res['analysis'][0]['name'] == 'rand'
