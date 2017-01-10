from __future__ import print_function

import json
import unittest
import os
from os import path
from fnmatch import fnmatch

from jsonschema import RefResolver, Draft4Validator, ValidationError

root_path = path.join(path.dirname(path.realpath(__file__)), '..')
schema_folder = path.join(root_path, 'senpy', 'schemas')
examples_path = path.join(root_path, 'docs', 'examples')
bad_examples_path = path.join(root_path, 'docs', 'bad-examples')


class JSONSchemaTests(unittest.TestCase):
    pass


def do_create_(jsfile, success):
    def do_expected(self):
        with open(jsfile) as f:
            js = json.load(f)
        try:
            assert '@type' in js
            schema_name = js['@type']
            with open(os.path.join(schema_folder, schema_name +
                                   ".json")) as file_object:
                schema = json.load(file_object)
            resolver = RefResolver('file://' + schema_folder + '/', schema)
            validator = Draft4Validator(schema, resolver=resolver)
            validator.validate(js)
        except (AssertionError, ValidationError, KeyError) as ex:
            if success:
                raise

    return do_expected


def add_examples(dirname, success):
    for dirpath, dirnames, filenames in os.walk(dirname):
        for i in filenames:
            if fnmatch(i, '*.json'):
                filename = path.join(dirpath, i)
                test_method = do_create_(filename, success)
                test_method.__name__ = 'test_file_%s_success_%s' % (filename,
                                                                    success)
                test_method.__doc__ = '%s should %svalidate' % (filename, ''
                                                                if success else
                                                                'not')
                setattr(JSONSchemaTests, test_method.__name__, test_method)
                del test_method


add_examples(examples_path, True)
add_examples(bad_examples_path, False)

if __name__ == '__main__':
    unittest.main()
