import logging

logger = logging.getLogger(__name__)

from unittest import TestCase
from senpy.api import (boolean, parse_params, get_extra_params, parse_analysis,
                       API_PARAMS, NIF_PARAMS, WEB_PARAMS)
from senpy.models import Error, Plugin


class APITest(TestCase):

    def test_api_params(self):
        """The API should not define any required parameters without a default"""
        parse_params({}, API_PARAMS)

    def test_web_params(self):
        """The WEB should not define any required parameters without a default"""
        parse_params({}, WEB_PARAMS)

    def test_basic(self):
        a = {}
        self.assertRaises(Error, parse_params, a)
        self.assertRaises(Error, parse_params, a, NIF_PARAMS)
        a = {'input': 'hello'}
        p = parse_params(a, NIF_PARAMS)
        assert 'input' in p
        b = {'i': 'hello'}
        p = parse_params(b, NIF_PARAMS)
        assert 'input' in p

    def test_plugin(self):
        query = {}
        plug_params = {
            'hello': {
                'aliases': ['hiya', 'hello'],
                'required': True
            }
        }
        self.assertRaises(Error, parse_params, plug_params)
        query['hello'] = 'world'
        p = parse_params(query, plug_params)
        assert 'hello' in p
        assert p['hello'] == 'world'
        del query['hello']

        query['hiya'] = 'dlrow'
        p = parse_params(query, plug_params)
        assert 'hello' in p
        assert p['hello'] == 'dlrow'

    def test_parameters2(self):
        in1 = {
            'meaningcloud-key': 5
        }
        in2 = {
            'apikey': 25
        }
        extra_params = {
            "apikey": {
                "aliases": [
                    "apikey",
                    "meaningcloud-key"
                ],
                "required": True
            }
        }
        p1 = parse_params(in1, extra_params)
        p2 = parse_params(in2, extra_params)
        assert (p2['apikey'] / p1['apikey']) == 5

    def test_default(self):
        spec = {
            'hello': {
                'required': True,
                'default': 1
            }
        }
        p = parse_params({}, spec)
        assert 'hello' in p
        assert p['hello'] == 1

    def test_call(self):
        call = {
            'input': "Aloha my friend",
            'algo': "Dummy"
        }
        p = parse_params(call, API_PARAMS, NIF_PARAMS)
        assert 'algorithm' in p
        assert "Dummy" in p['algorithm']
        assert 'input' in p
        assert p['input'] == 'Aloha my friend'

    def test_parse_analysis(self):
        '''The API should parse user parameters and return them in a format that plugins can use'''
        plugins = [
            Plugin({
                'name': 'plugin1',
                'extra_params': {
                    # Incompatible parameter
                    'param0': {
                        'aliases': ['p1', 'parameter1'],
                        'options': ['option1', 'option2'],
                        'default': 'option1',
                        'required': True
                    },
                    'param1': {
                        'aliases': ['p1', 'parameter1'],
                        'options': ['en', 'es'],

                        'default': 'en',
                        'required': False
                    },
                    'param2': {
                        'aliases': ['p2', 'parameter2'],
                        'required': False,
                        'options': ['value2_1', 'value2_2', 'value3_3']
                    }
                }
            }), Plugin({
                'name': 'plugin2',
                'extra_params': {
                    'param0': {
                        'aliases': ['parameter1'],
                        'options': ['new option', 'new option2'],
                        'default': 'new option',
                        'required': False
                    },
                    'param1': {
                        'aliases': ['myparam1', 'p1'],
                        'options': ['en', 'de', 'auto'],
                        'default': 'de',
                        'required': True
                    },
                    'param3': {
                        'aliases': ['p3', 'parameter3'],
                        'options': boolean,
                        'default': True
                    }
                }
            })
        ]
        call = {
            'param1': 'en',
            '0.param0': 'option1',
            '0.param1': 'en',
            'param2': 'value2_1',
            'param0': 'new option',
            '1.param1': 'de',
            'param3': False,
        }
        expected = [
            {
                'param0': 'option1',
                'param1': 'en',
                'param2': 'value2_1',
            }, {
                'param0': 'new option',
                'param1': 'de',
                'param3': False,
            }

        ]
        p = parse_analysis(call, plugins)
        for i, arg in enumerate(expected):
            params = p[i].params
            for k, v in arg.items():
                assert params[k] == v

    def test_get_extra_params(self):
        '''The API should return the list of valid parameters for a set of plugins'''
        plugins = [
            Plugin({
                'name': 'plugin1',
                'extra_params': {
                    # Incompatible parameter
                    'param0': {
                        'aliases': ['p1', 'parameter1'],
                        'options': ['option1', 'option2'],
                        'default': 'option1',
                        'required': True
                    },
                    'param1': {
                        'aliases': ['p1', 'parameter1'],
                        'options': ['en', 'es'],
                        'default': 'en',
                        'required': False
                    },
                    'param2': {
                        'aliases': ['p2', 'parameter2'],
                        'required': False,
                        'options': ['value2_1', 'value2_2', 'value3_3']
                    }
                }
            }), Plugin({
                'name': 'plugin2',
                'extra_params': {
                    'param0': {
                        'aliases': ['parameter1'],
                        'options': ['new option', 'new option2'],
                        'default': 'new option',
                        'required': False
                    },
                    'param1': {
                        'aliases': ['myparam1', 'p1'],
                        'options': ['en', 'de', 'auto'],
                        'default': 'de',
                        'required': True
                    },
                    'param3': {
                        'aliases': ['p3', 'parameter3'],
                        'options': boolean,
                        'default': True
                    }
                }
            })
        ]

        expected = {
            # Overlapping parameters
            'plugin1.param0': plugins[0]['extra_params']['param0'],
            'plugin1.param1': plugins[0]['extra_params']['param1'],
            'plugin2.param0': plugins[1]['extra_params']['param0'],
            'plugin2.param1': plugins[1]['extra_params']['param1'],

            # Non-overlapping parameters
            'param2': plugins[0]['extra_params']['param2'],
            'param3': plugins[1]['extra_params']['param3'],

            # Intersection of overlapping parameters
            'param1': {
                'aliases': ['p1'],
                'options': ['en'],
                'default': None,
                'required': True
            }
        }

        result = get_extra_params(plugins)

        for ik, iv in expected.items():
            assert ik in result
            for jk, jv in iv.items():
                assert jk in result[ik]
                assert expected[ik][jk] == result[ik][jk]
