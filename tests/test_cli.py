import logging
from functools import partial

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

logger = logging.getLogger(__name__)

from unittest import TestCase
from senpy.cli import main_function
from senpy.models import Error


class CLITest(TestCase):
    def test_basic(self):
        self.assertRaises(Error, partial(main_function, []))

        with patch('senpy.extensions.Senpy.analyse') as patched:
            main_function(['--input', 'test'])

        patched.assert_called_with(input='test')
        with patch('senpy.extensions.Senpy.analyse') as patched:
            main_function(['--input', 'test', '--algo', 'rand'])

        patched.assert_called_with(input='test', algo='rand')
