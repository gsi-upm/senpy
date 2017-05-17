'''
Senpy Models.

This implementation should mirror the JSON schema definition.
For compatibility with Py3 and for easier debugging, this new version drops
introspection and adds all arguments to the models.
'''
from __future__ import print_function
from six import string_types

import time
import copy
import json
import os
import jsonref
import jsonschema

from flask import Response as FlaskResponse
from pyld import jsonld

from rdflib import Graph

import logging

logger = logging.getLogger(__name__)

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


base_schema = read_schema(DEFINITIONS_FILE)


class Context(dict):
    @staticmethod
    def load(context):
        logging.debug('Loading context: {}'.format(context))
        if not context:
            return context
        elif isinstance(context, list):
            contexts = []
            for c in context:
                contexts.append(Context.load(c))
            return contexts
        elif isinstance(context, dict):
            return Context(context)
        elif isinstance(context, string_types):
            try:
                with open(context) as f:
                    return Context(json.loads(f.read()))
            except IOError:
                return context
        else:
            raise AttributeError('Please, provide a valid context')


base_context = Context.load(CONTEXT_PATH)


class SenpyMixin(object):
    _context = base_context["@context"]

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
            status=getattr(self, "status", 200),
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
            elif isinstance(item, list):
                return list(ser_or_down(i) for i in item)
            else:
                return item

        return ser_or_down(self._plain_dict())

    def jsonld(self,
               with_context=True,
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
        jsonschema.validate(obj, self.schema)

    def __str__(self):
        return str(self.to_JSON())


class BaseModel(SenpyMixin, dict):

    schema = base_schema

    def __init__(self, *args, **kwargs):
        if 'id' in kwargs:
            self.id = kwargs.pop('id')
        elif kwargs.pop('_auto_id', True):
            self.id = '_:{}_{}'.format(type(self).__name__, time.time())
        temp = dict(*args, **kwargs)

        for obj in [
                self.schema,
        ] + self.schema.get('allOf', []):
            for k, v in obj.get('properties', {}).items():
                if 'default' in v and k not in temp:
                    temp[k] = copy.deepcopy(v['default'])

        for i in temp:
            nk = self._get_key(i)
            if nk != i:
                temp[nk] = temp[i]
                del temp[i]
        try:
            temp['@type'] = getattr(self, '@type')
        except AttributeError:
            logger.warn('Creating an instance of an unknown model')

        super(BaseModel, self).__init__(temp)

    def _get_key(self, key):
        key = key.replace("__", ":", 1)
        return key

    def __setitem__(self, key, value):
        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __getattr__(self, key):
        try:
            return self.__getitem__(self._get_key(key))
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self.__setitem__(self._get_key(key), value)

    def __delattr__(self, key):
        try:
            object.__delattr__(self, key)
        except AttributeError:
            self.__delitem__(self._get_key(key))

    def _plain_dict(self):
        d = {k: v for (k, v) in self.items() if k[0] != "_"}
        if 'id' in d:
            d["@id"] = d.pop('id')
        return d


_subtypes = {}


def register(rsubclass, rtype=None):
    _subtypes[rtype or rsubclass.__name__] = rsubclass


def from_dict(indict, cls=None):
    if not cls:
        target = indict.get('@type', None)
        try:
            if target and target in _subtypes:
                cls = _subtypes[target]
            else:
                cls = BaseModel
        except Exception:
            cls = BaseModel
    outdict = dict()
    for k, v in indict.items():
        if k == '@context':
            pass
        elif isinstance(v, dict):
            v = from_dict(indict[k])
        elif isinstance(v, list):
            for ix, v2 in enumerate(v):
                if isinstance(v2, dict):
                    v[ix] = from_dict(v2)
        outdict[k] = v
    return cls(**outdict)


def from_string(string, **kwargs):
    return from_dict(json.loads(string), **kwargs)


def from_json(injson):
    indict = json.loads(injson)
    return from_dict(indict)


def from_schema(name, schema_file=None, base_classes=None):
    base_classes = base_classes or []
    base_classes.append(BaseModel)
    schema_file = schema_file or '{}.json'.format(name)
    class_name = '{}{}'.format(name[0].upper(), name[1:])
    newclass = type(class_name, tuple(base_classes), {})
    setattr(newclass, '@type', name)
    setattr(newclass, 'schema', read_schema(schema_file))
    setattr(newclass, 'class_name', class_name)
    register(newclass, name)
    return newclass


def _add_from_schema(*args, **kwargs):
    generatedClass = from_schema(*args, **kwargs)
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
        'entry',
        'plugin',
        'plugins',
        'response',
        'results',
        'sentiment',
        'sentimentPlugin',
        'suggestion',
]:
    _add_from_schema(i)

_ErrorModel = from_schema('error')


class Error(SenpyMixin, Exception):
    def __init__(self, message, *args, **kwargs):
        super(Error, self).__init__(self, message, message)
        self._error = _ErrorModel(message=message, *args, **kwargs)
        self.message = message

    def __getitem__(self, key):
        return self._error[key]

    def __setitem__(self, key, value):
        self._error[key] = value

    def __delitem__(self, key):
        del self._error[key]

    def __getattr__(self, key):
        if key != '_error' and hasattr(self._error, key):
            return getattr(self._error, key)
        raise AttributeError(key)

    def __setattr__(self, key, value):
        if key != '_error':
            return setattr(self._error, key, value)
        else:
            super(Error, self).__setattr__(key, value)

    def __delattr__(self, key):
        delattr(self._error, key)

    def __str__(self):
        return str(self.to_JSON(with_context=False))


register(Error, 'error')
