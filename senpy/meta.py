'''
Meta-programming for the models.
'''
import os
import json
import jsonschema
import inspect
import copy

from abc import ABCMeta


class BaseMeta(ABCMeta):
    '''
    Metaclass for models. It extracts the default values for the fields in
    the model.

    For instance, instances of the following class wouldn't need to mark
    their version or description on initialization:

    .. code-block:: python

       class MyPlugin(Plugin):
           version=0.3
           description='A dull plugin'


    Note that these operations could be included in the __init__ of the
    class, but it would be very inefficient.
    '''
    _subtypes = {}

    def __new__(mcs, name, bases, attrs, **kwargs):
        defaults = {}
        register_afterwards = False

        attrs = mcs.expand_with_schema(name, attrs)
        if 'schema' in attrs:
            register_afterwards = True
            defaults = mcs.get_defaults(attrs['schema'])
        for b in bases:
            if hasattr(b, '_defaults'):
                defaults.update(b._defaults)
        info, attrs = mcs.split_attrs(attrs)
        defaults.update(info)
        attrs['_defaults'] = defaults

        cls = super(BaseMeta, mcs).__new__(mcs, name, tuple(bases), attrs)

        if register_afterwards:
            mcs.register(cls, cls._defaults['@type'])
        return cls

    @classmethod
    def register(mcs, rsubclass, rtype=None):
        mcs._subtypes[rtype or rsubclass.__name__] = rsubclass

    @staticmethod
    def expand_with_schema(name, attrs):
        if 'schema' in attrs:  # Schema specified by name
            schema_file = '{}.json'.format(attrs['schema'])
        elif 'schema_file' in attrs:
            schema_file = attrs['schema_file']
            del attrs['schema_file']
        else:
            return attrs

        if '/' not in 'schema_file':
            thisdir = os.path.dirname(os.path.realpath(__file__))
            schema_file = os.path.join(thisdir,
                                       'schemas',
                                       schema_file)

        schema_path = 'file://' + schema_file

        with open(schema_file) as f:
            schema = json.load(f)

        resolver = jsonschema.RefResolver(schema_path, schema)
        attrs['@type'] = "".join((name[0].lower(), name[1:]))
        attrs['_schema_file'] = schema_file
        attrs['schema'] = schema
        attrs['_validator'] = jsonschema.Draft4Validator(schema, resolver=resolver)
        return attrs

    @staticmethod
    def is_attr(k, v):
        return (not(inspect.isroutine(v) or
                    inspect.ismethod(v) or
                    inspect.ismodule(v) or
                    isinstance(v, property)) and
                k[0] != '_' and
                k != 'schema' and
                k != 'data')

    @staticmethod
    def split_attrs(attrs):
        '''
        Extract the attributes of the class.

        This allows adding default values in the class definition.
        e.g.:
        '''
        isattr = {}
        notattr = {}
        for key, value in attrs.items():
            if BaseMeta.is_attr(key, value):
                if key[0] != '_':
                    key = key.replace("__", ":", 1)
                isattr[key] = copy.deepcopy(value)
            else:
                notattr[key] = value
        return isattr, notattr

    @staticmethod
    def get_defaults(schema):
        temp = {}
        for obj in [
                schema,
        ] + schema.get('allOf', []):
            for k, v in obj.get('properties', {}).items():
                if 'default' in v and k not in temp:
                    temp[k] = copy.deepcopy(v['default'])
        return temp
