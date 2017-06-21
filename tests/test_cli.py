import logging
from functools import partial

logger = logging.getLogger(__name__)

from unittest import TestCase
from senpy.cli import main_function
from senpy.models import Error


class CLITest(TestCase):
    def test_basic(self):
        self.assertRaises(Error, partial(main_function, []))

        res = main_function(['--input', 'test', '--algo', 'rand', '--with-parameters'])
        assert res.parameters['input'] == 'test'
        assert 'rand' in res.parameters['algorithm']
        assert res.parameters['input'] == 'test'
