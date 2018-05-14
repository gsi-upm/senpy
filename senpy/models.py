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
from flask import Response as FlaskResponse
from pyld import jsonld

import logging

logging.getLogger('rdflib').setLevel(logging.WARN)
logger = logging.getLogger(__name__)

from rdflib import Graph


from .meta import BaseMeta, CustomDict, alias

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


def dump_schema(schema):
    return jsonref.dumps(schema)


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

        if auto_id:
            self.id

        if '@type' not in self:
            logger.warn('Created an instance of an unknown model')

    @property
    def id(self):
        if '@id' not in self:
            self['@id'] = ':{}_{}'.format(type(self).__name__, time.time())
        return self['@id']

    @id.setter
    def id(self, value):
        self['@id'] = value

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

    def validate(self, obj=None):
        if not obj:
            obj = self
        if hasattr(obj, "jsonld"):
            obj = obj.jsonld()
        self._validator.validate(obj)

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
        outdict[k] = copy.copy(v)
    return cls(**outdict)


def from_string(string, **kwargs):
    return from_dict(json.loads(string), **kwargs)


def from_json(injson):
    indict = json.loads(injson)
    return from_dict(indict)


class Entry(BaseModel):
    schema = 'entry'

    text = alias('nif:isString')


class Sentiment(BaseModel):
    schema = 'sentiment'

    polarity = alias('marl:hasPolarity')
    polarityValue = alias('marl:hasPolarityValue')


class Error(BaseModel, Exception):
    schema = 'error'

    def __init__(self, message='Generic senpy exception', *args, **kwargs):
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
        'entity',
        'help',
        'plugin',
        'plugins',
        'response',
        'results',
        'sentimentPlugin',
        'suggestion',
        'aggregatedEvaluation',
        'evaluation',
        'metric',
        'dataset',
        'datasets',

]:
    _add_class_from_schema(i)
