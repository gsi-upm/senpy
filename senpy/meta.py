#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
'''
Meta-programming for the models.
'''
import os
import json
import jsonschema
import inspect
import copy

from abc import ABCMeta
from collections import namedtuple
from collections.abc import MutableMapping


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
        register_afterwards = False
        defaults = {}
        aliases = {}

        attrs = mcs.expand_with_schema(name, attrs)
        if 'schema' in attrs:
            register_afterwards = True
        for base in bases:
            if hasattr(base, '_defaults'):
                defaults.update(getattr(base, '_defaults'))
            if hasattr(base, '_aliases'):
                aliases.update(getattr(base, '_aliases'))

        info, rest = mcs.split_attrs(attrs)

        for i in list(info.keys()):
            if isinstance(info[i], _Alias):
                aliases[i] = info[i].indict
                if info[i].default is not None:
                    defaults[i] = info[i].default
            else:
                defaults[i] = info[i]

        rest['_defaults'] = defaults
        rest['_aliases'] = aliases

        cls = super(BaseMeta, mcs).__new__(mcs, name, tuple(bases), rest)

        if register_afterwards:
            mcs.register(cls, defaults['@type'])
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
        if '@type' not in attrs:
            attrs['@type'] = name
        attrs['_schema_file'] = schema_file
        attrs['schema'] = schema
        attrs['_validator'] = jsonschema.Draft4Validator(schema, resolver=resolver)

        schema_defaults = BaseMeta.get_defaults(attrs['schema'])
        attrs.update(schema_defaults)

        return attrs

    @staticmethod
    def is_func(v):
        return inspect.isroutine(v) or inspect.ismethod(v) or \
            inspect.ismodule(v) or isinstance(v, property)

    @staticmethod
    def is_internal(k):
        return k[0] == '_' or k == 'schema' or k == 'data'

    @staticmethod
    def get_key(key):
        if key[0] != '_':
            key = key.replace("__", ":", 1)
        return key

    @staticmethod
    def split_attrs(attrs):
        '''
        Extract the attributes of the class.

        This allows adding default values in the class definition.
        e.g.:
        '''
        isattr = {}
        rest = {}
        for key, value in attrs.items():
            if not (BaseMeta.is_internal(key)) and (not BaseMeta.is_func(value)):
                isattr[key] = value
            else:
                rest[key] = value
        return isattr, rest

    @staticmethod
    def get_defaults(schema):
        temp = {}
        for obj in [
                schema,
        ] + schema.get('allOf', []):
            for k, v in obj.get('properties', {}).items():
                if 'default' in v and k not in temp:
                    temp[k] = v['default']
        return temp


def make_property(key, default=None):

    def fget(self):
        if default:
            return self.get(key, copy.copy(default))
        return self[key]

    def fdel(self):
        del self[key]

    def fset(self, value):
        self[key] = value

    return fget, fset, fdel


class CustomDict(MutableMapping, object):
    '''
    A dictionary whose elements can also be accessed as attributes. Since some
    characters are not valid in the dot-notation, the attribute names also
    converted. e.g.:

    > d = CustomDict()
    > d.key = d['ns:name'] = 1
    > d.key == d['key']
    True
    > d.ns__name == d['ns:name']
    '''

    _defaults = {}
    _aliases = {'id': '@id'}

    def __init__(self, *args, **kwargs):
        super(CustomDict, self).__init__()
        for k, v in self._defaults.items():
            self[k] = copy.copy(v)
        for arg in args:
            self.update(arg)
        for k, v in kwargs.items():
            self[k] = v
        return self

    def serializable(self, **kwargs):
        def ser_or_down(item):
            if hasattr(item, 'serializable'):
                return item.serializable(**kwargs)
            elif isinstance(item, dict):
                temp = dict()
                for kp in item:
                    vp = item[kp]
                    temp[kp] = ser_or_down(vp)
                return temp
            elif isinstance(item, list) or isinstance(item, set):
                return list(ser_or_down(i) for i in item)
            else:
                return item

        return ser_or_down(self.as_dict(**kwargs))

    def __getitem__(self, key):
        return self.__dict__[key]

    def __setitem__(self, key, value):
        '''Do not insert data directly, there might be a property in that key. '''
        key = self._key_to_attr(key)
        return setattr(self, key, value)

    def __delitem__(self, key):
        key = self._key_to_attr(key)
        del self.__dict__[key]

    def as_dict(self, verbose=True, aliases=False):
        attrs = self.__dict__.keys()
        if not verbose and hasattr(self, '_terse_keys'):
            attrs = self._terse_keys + ['@type', '@id']
        res = {k: getattr(self, k) for k in attrs
               if not self._internal_key(k) and hasattr(self, k)}
        if not aliases:
            return res
        for k, ok in self._aliases.items():
            if ok in res:
                res[k] = getattr(res, ok)
                del res[ok]
        return res

    def __iter__(self):
        return (k for k in self.__dict__ if not self._internal_key(k))

    def __len__(self):
        return len(self.__dict__)

    def update(self, other):
        for k, v in other.items():
            self[k] = v

    def _attr_to_key(self, key):
        key = key.replace("__", ":", 1)
        key = self._aliases.get(key, key)
        return key

    def _key_to_attr(self, key):
        if self._internal_key(key):
            return key

        if key in self._aliases:
            key = self._aliases[key]
        else:
            key = key.replace(":", "__", 1)
        return key

    def __getattr__(self, key):
        nkey = self._attr_to_key(key)
        if nkey in self.__dict__:
            return self.__dict__[nkey]
        elif nkey == key:
            raise AttributeError("Key not found: {}".format(key))
        return getattr(self, nkey)

    def __setattr__(self, key, value):
        super(CustomDict, self).__setattr__(self._attr_to_key(key), value)

    def __delattr__(self, key):
        super(CustomDict, self).__delattr__(self._attr_to_key(key))

    @staticmethod
    def _internal_key(key):
        return key[0] == '_'

    def __str__(self):
        return json.dumps(self.serializable(), sort_keys=True, indent=4)

    def __repr__(self):
        return json.dumps(self.serializable(), sort_keys=True, indent=4)


_Alias = namedtuple('Alias', ['indict', 'default'])


def alias(key, default=None):
    return _Alias(key, default)
