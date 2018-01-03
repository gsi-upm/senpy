'''
Senpy Models.

This implementation should mirror the JSON schema definition.
For compatibility with Py3 and for easier debugging, this new version drops
introspection and adds all arguments to the models.
'''
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()

from future.utils import with_metaclass
from past.builtins import basestring

import time
import copy
import json
import os
import jsonref
from collections import UserDict

from flask import Response as FlaskResponse
from pyld import jsonld

import logging

logging.getLogger('rdflib').setLevel(logging.WARN)
logger = logging.getLogger(__name__)

from rdflib import Graph


from .meta import BaseMeta

DEFINITIONS_FILE = 'definitions.json'
CONTEXT_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'schemas', 'context.jsonld')


def get_schema_path(schema_file, absolute=False):
    if absolute:
        return os.path.realpath(schema_file)
    else:
        return os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'schemas',
            schema_file)


def read_schema(schema_file, absolute=False):
    schema_path = get_schema_path(schema_file, absolute)
    schema_uri = 'file://{}'.format(schema_path)
    with open(schema_path) as f:
        return jsonref.load(f, base_uri=schema_uri)


def load_context(context):
    logging.debug('Loading context: {}'.format(context))
    if not context:
        return context
    elif isinstance(context, list):
        contexts = []
        for c in context:
            contexts.append(load_context(c))
        return contexts
    elif isinstance(context, dict):
        return dict(context)
    elif isinstance(context, basestring):
        try:
            with open(context) as f:
                return dict(json.loads(f.read()))
        except IOError:
            return context
    else:
        raise AttributeError('Please, provide a valid context')


base_context = load_context(CONTEXT_PATH)


def register(rsubclass, rtype=None):
    BaseMeta.register(rsubclass, rtype)


class CustomDict(UserDict, object):
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

    _defaults = []

    def __init__(self, *args, **kwargs):
        temp = copy.deepcopy(self._defaults)
        for arg in args:
            temp.update(copy.deepcopy(arg))
        for k, v in kwargs.items():
            temp[self._get_key(k)] = v

        super(CustomDict, self).__init__(temp)

    @staticmethod
    def _get_key(key):
        if key is 'id':
            key = '@id'
        key = key.replace("__", ":", 1)
        return key

    @staticmethod
    def _internal_key(key):
        return key[0] == '_' or key == 'data'

    def __getattr__(self, key):
        '''
        __getattr__ only gets called when the attribute could not be found
        in the __dict__. So we only need to look for the the element in the
        dictionary, or raise an Exception.
        '''
        mkey = self._get_key(key)
        if not self._internal_key(key) and mkey in self:
            return self[mkey]
        raise AttributeError(key)

    def __setattr__(self, key, value):
        # Work as usual for internal properties or already existing
        # properties
        if self._internal_key(key) or key in self.__dict__:
            return super(CustomDict, self).__setattr__(key, value)
        key = self._get_key(key)
        return self.__setitem__(self._get_key(key), value)

    def __delattr__(self, key):
        if self._internal_key(key):
            return object.__delattr__(self, key)
        key = self._get_key(key)
        self.__delitem__(self._get_key(key))


class BaseModel(with_metaclass(BaseMeta, CustomDict)):
    '''
    Entities of the base model are a special kind of dictionary that emulates
    a JSON-LD object. The structure of the dictionary is checked via JSON-schema.
    For convenience, the values can also be accessed as attributes
    (a la Javascript). e.g.:

    >>> myobject.key == myobject['key']
    True
    >>> myobject.ns__name == myobject['ns:name']
    True

    Additionally, subclasses of this class can specify default values for their
    instances. These defaults are inherited by subclasses. e.g.:

    >>> class NewModel(BaseModel):
    ...     mydefault = 5
    >>> n1 = NewModel()
    >>> n1['mydefault'] == 5
    True
    >>> n1.mydefault = 3
    >>> n1['mydefault'] = 3
    True
    >>> n2 = NewModel()
    >>> n2 == 5
    True
    >>> class SubModel(NewModel):
            pass
    >>> subn = SubModel()
    >>> subn.mydefault == 5
    True

    Lastly, every subclass that also specifies a schema will get registered, so it
    is possible to deserialize JSON and get the right type.
    i.e. to recover an instance of the original class from a plain JSON.

    '''

    schema_file = DEFINITIONS_FILE
    _context = base_context["@context"]

    def __init__(self, *args, **kwargs):
        auto_id = kwargs.pop('_auto_id', True)
        super(BaseModel, self).__init__(*args, **kwargs)

        if '@id' not in self and auto_id:
            self.id = ':{}_{}'.format(type(self).__name__, time.time())

        if '@type' not in self:
            logger.warn('Created an instance of an unknown model')

    def flask(self,
              in_headers=True,
              headers=None,
              outformat='json-ld',
              **kwargs):
        """
        Return the values and error to be used in flask.
        So far, it returns a fixed context. We should store/generate different
        contexts if the plugin adds more aliases.
        """
        headers = headers or {}
        kwargs["with_context"] = not in_headers
        content, mimetype = self.serialize(format=outformat,
                                           with_mime=True,
                                           **kwargs)

        if outformat == 'json-ld' and in_headers:
            headers.update({
                "Link":
                ('<%s>;'
                    'rel="http://www.w3.org/ns/json-ld#context";'
                    ' type="application/ld+json"' % kwargs.get('context_uri'))
            })
        return FlaskResponse(
            response=content,
            status=self.get('status', 200),
            headers=headers,
            mimetype=mimetype)

    def serialize(self, format='json-ld', with_mime=False, **kwargs):
        js = self.jsonld(**kwargs)
        if format == 'json-ld':
            content = json.dumps(js, indent=2, sort_keys=True)
            mimetype = "application/json"
        elif format in ['turtle', ]:
            logger.debug(js)
            content = json.dumps(js, indent=2, sort_keys=True)
            g = Graph().parse(
                data=content,
                format='json-ld',
                base=kwargs.get('prefix'),
                context=self._context)
            logger.debug(
                'Parsing with prefix: {}'.format(kwargs.get('prefix')))
            content = g.serialize(format='turtle').decode('utf-8')
            mimetype = 'text/{}'.format(format)
        else:
            raise Error('Unknown outformat: {}'.format(format))
        if with_mime:
            return content, mimetype
        else:
            return content

    def serializable(self):
        def ser_or_down(item):
            if hasattr(item, 'serializable'):
                return item.serializable()
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

        return ser_or_down(self.data)

    def jsonld(self,
               with_context=False,
               context_uri=None,
               prefix=None,
               expanded=False):
        ser = self.serializable()

        result = jsonld.compact(
            ser,
            self._context,
            options={
                'base': prefix,
                'expandContext': self._context,
                'senpy': prefix
            })
        if context_uri:
            result['@context'] = context_uri
        if expanded:
            result = jsonld.expand(
                result, options={'base': prefix,
                                 'expandContext': self._context})
        if not with_context:
            del result['@context']
        return result

    def to_JSON(self, *args, **kwargs):
        js = json.dumps(self.jsonld(*args, **kwargs), indent=4, sort_keys=True)
        return js

    def validate(self, obj=None):
        if not obj:
            obj = self
        if hasattr(obj, "jsonld"):
            obj = obj.jsonld()
        self._validator.validate(obj)

    def __str__(self):
        return str(self.serialize())

    def prov(self, another):
        self['prov:wasGeneratedBy'] = another.id


def subtypes():
    return BaseMeta._subtypes


def from_dict(indict, cls=None):
    if not cls:
        target = indict.get('@type', None)
        cls = BaseModel
        try:
            cls = subtypes()[target]
        except KeyError:
            pass
    outdict = dict()
    for k, v in indict.items():
        if k == '@context':
            pass
        elif isinstance(v, dict):
            v = from_dict(indict[k])
        elif isinstance(v, list):
            v = v[:]
            for ix, v2 in enumerate(v):
                if isinstance(v2, dict):
                    v[ix] = from_dict(v2)
        outdict[k] = copy.deepcopy(v)
    return cls(**outdict)


def from_string(string, **kwargs):
    return from_dict(json.loads(string), **kwargs)


def from_json(injson):
    indict = json.loads(injson)
    return from_dict(indict)


class Entry(BaseModel, Exception):
    schema = 'entry'

    @property
    def text(self):
        return self['nif:isString']

    @text.setter
    def text(self, value):
        self['nif:isString'] = value


class Error(BaseModel, Exception):
    schema = 'error'

    def __init__(self, message, *args, **kwargs):
        Exception.__init__(self, message)
        super(Error, self).__init__(*args, **kwargs)
        self.message = message

    def __str__(self):
        if not hasattr(self, 'errors'):
            return self.message
        return '{}:\n\t{}'.format(self.message, self.errors)

    def __hash__(self):
        return Exception.__hash__(self)


# Add the remaining schemas programmatically

def _class_from_schema(name, schema=None, schema_file=None, base_classes=None):
    base_classes = base_classes or []
    base_classes.append(BaseModel)
    attrs = {}
    if schema:
        attrs['schema'] = schema
    elif schema_file:
        attrs['schema_file'] = schema_file
    else:
        attrs['schema'] = name
    name = "".join((name[0].upper(), name[1:]))
    return BaseMeta(name, base_classes, attrs)


def _add_class_from_schema(*args, **kwargs):
    generatedClass = _class_from_schema(*args, **kwargs)
    globals()[generatedClass.__name__] = generatedClass
    del generatedClass


for i in [
        'analysis',
        'emotion',
        'emotionConversion',
        'emotionConversionPlugin',
        'emotionAnalysis',
        'emotionModel',
        'emotionPlugin',
        'emotionSet',
        'help',
        'plugin',
        'plugins',
        'response',
        'results',
        'sentiment',
        'sentimentPlugin',
        'suggestion',
]:
    _add_class_from_schema(i)
