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
    context = base_context["@context"]

    def flask(self, in_headers=True, headers=None, **kwargs):
        """
        Return the values and error to be used in flask.
        So far, it returns a fixed context. We should store/generate different
        contexts if the plugin adds more aliases.
        """
        headers = headers or {}
        kwargs["with_context"] = True
        js = self.jsonld(**kwargs)
        if in_headers:
            url = js["@context"]
            del js["@context"]
            headers.update({
                "Link": ('<%s>;'
                         'rel="http://www.w3.org/ns/json-ld#context";'
                         ' type="application/ld+json"' % url)
            })
        return FlaskResponse(
            json.dumps(
                js, indent=2, sort_keys=True),
            status=getattr(self, "status", 200),
            headers=headers,
            mimetype="application/json")

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

    def jsonld(self, with_context=True, context_uri=None):
        ser = self.serializable()

        if with_context:
            context = []
            if context_uri:
                context = context_uri
            else:
                context = self.context.copy()
            if hasattr(self, 'prefix'):
                # This sets @base for the document, which will be used in
                # all relative URIs. For example, if a uri is "Example" and
                # prefix =s "http://example.com", the absolute URI after
                # expanding with JSON-LD will be "http://example.com/Example"

                prefix_context = {"@base": self.prefix}
                if isinstance(context, list):
                    context.append(prefix_context)
                else:
                    context = [context, prefix_context]
            ser["@context"] = context
        return ser

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
            self.id = '_:{}_{}'.format(
                type(self).__name__, time.time())
        temp = dict(*args, **kwargs)

        for obj in [self.schema, ] + self.schema.get('allOf', []):
            for k, v in obj.get('properties', {}).items():
                if 'default' in v:
                    temp[k] = copy.deepcopy(v['default'])

        for i in temp:
            nk = self._get_key(i)
            if nk != i:
                temp[nk] = temp[i]
                del temp[i]
        if 'context' in temp:
            context = temp['context']
            del temp['context']
            self.__dict__['context'] = Context.load(context)
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
        self.__delitem__(self._get_key(key))

    def _plain_dict(self):
        d = {k: v for (k, v) in self.items() if k[0] != "_"}
        if 'id' in d:
            d["@id"] = d.pop('id')
        return d


_subtypes = {}


def register(rsubclass, rtype=None):
    _subtypes[rtype or rsubclass.__name__] = rsubclass


def from_dict(indict):
    target = indict.get('@type', None)
    if target and target in _subtypes:
        cls = _subtypes[target]
    else:
        cls = BaseModel
    return cls(**indict)


def from_schema(name, schema_file=None, base_classes=None):
    base_classes = base_classes or []
    base_classes.append(BaseModel)
    schema_file = schema_file or '{}.json'.format(name)
    class_name = '{}{}'.format(i[0].upper(), i[1:])
    newclass = type(class_name, tuple(base_classes), {})
    setattr(newclass, '@type', name)
    setattr(newclass, 'schema', read_schema(schema_file))
    register(newclass, name)
    return newclass


def _add_from_schema(*args, **kwargs):
    generatedClass = from_schema(*args, **kwargs)
    globals()[generatedClass.__name__] = generatedClass
    del generatedClass


for i in ['response',
          'results',
          'entry',
          'sentiment',
          'analysis',
          'emotionSet',
          'emotion',
          'emotionModel',
          'suggestion',
          'plugin',
          'emotionPlugin',
          'sentimentPlugin',
          'plugins']:
    _add_from_schema(i)

_ErrorModel = from_schema('error')


class Error(SenpyMixin, BaseException):
    def __init__(self,
                 message,
                 *args,
                 **kwargs):
        super(Error, self).__init__(self, message, message)
        self._error = _ErrorModel(message=message, *args, **kwargs)
        self.message = message

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


register(Error, 'error')
