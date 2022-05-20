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

from jinja2 import Environment, BaseLoader

import time
import copy
import json
import os
import jsonref
from flask import Response as FlaskResponse
from pyld import jsonld

import logging
import jmespath

logging.getLogger('rdflib').setLevel(logging.WARN)
logger = logging.getLogger(__name__)

from rdflib import Graph


from .meta import BaseMeta, CustomDict, alias

DEFINITIONS_FILE = 'definitions.json'
CONTEXT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'schemas',
                            'context.jsonld')


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

    # schema_file = DEFINITIONS_FILE
    _context = base_context["@context"]

    def __init__(self, *args, **kwargs):
        auto_id = kwargs.pop('_auto_id', False)

        super(BaseModel, self).__init__(*args, **kwargs)

        if auto_id:
            self.id

    @property
    def id(self):
        if '@id' not in self:
            self['@id'] = 'prefix:{}_{}'.format(type(self).__name__, time.time())
        return self['@id']

    @id.setter
    def id(self, value):
        self['@id'] = value

    def flask(self,
              in_headers=False,
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

    def serialize(self, format='json-ld', with_mime=False,
                  template=None, prefix=None, fields=None, **kwargs):
        js = self.jsonld(prefix=prefix, **kwargs)
        if template is not None:
            rtemplate = Environment(loader=BaseLoader).from_string(template)
            content = rtemplate.render(**self)
            mimetype = 'text'
        elif fields is not None:
            # Emulate field selection by constructing a template
            content = json.dumps(jmespath.search(fields, js))
            mimetype = 'text'
        elif format == 'json-ld':
            content = json.dumps(js, indent=2, sort_keys=True)
            mimetype = "application/json"
        elif format in ['turtle', 'ntriples']:
            content = json.dumps(js, indent=2, sort_keys=True)
            logger.debug(js)
            context = [self._context, {'prefix': prefix, '@base': prefix}]
            g = Graph().parse(
                data=content,
                format='json-ld',
                prefix=prefix,
                context=context)
            logger.debug(
                'Parsing with prefix: {}'.format(kwargs.get('prefix')))
            content = g.serialize(format=format,
                                  prefix=prefix)
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
               base=None,
               expanded=False,
               **kwargs):

        result = self.serializable(**kwargs)

        if expanded:
            result = jsonld.expand(
                result,
                options={
                    'expandContext': [
                        self._context,
                        {
                            'prefix': prefix,
                            'endpoint': prefix
                        }
                    ]
                }
            )[0]
        if not with_context:
            try:
                del result['@context']
            except KeyError:
                pass
        elif context_uri:
            result['@context'] = context_uri
        else:
            result['@context'] = self._context

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


def from_dict(indict, cls=None, warn=True):
    if not cls:
        target = indict.get('@type', None)
        cls = BaseModel
        try:
            cls = subtypes()[target]
        except KeyError:
            pass

    if cls == BaseModel and warn:
        logger.warning('Created an instance of an unknown model')

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


def from_json(injson, **kwargs):
    indict = json.loads(injson)
    return from_dict(indict, **kwargs)


class Entry(BaseModel):
    schema = 'entry'

    text = alias('nif:isString')
    sentiments = alias('marl:hasOpinion', [])
    emotions = alias('onyx:hasEmotionSet', [])


class Sentiment(BaseModel):
    schema = 'sentiment'

    polarity = alias('marl:hasPolarity')
    polarityValue = alias('marl:polarityValue')


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


class AggregatedEvaluation(BaseModel):
    schema = 'aggregatedEvaluation'

    evaluations = alias('senpy:evaluations', [])


class Dataset(BaseModel):
    schema = 'dataset'


class Datasets(BaseModel):
    schema = 'datasets'

    datasets = []


class Emotion(BaseModel):
    schema = 'emotion'


class EmotionConversion(BaseModel):
    schema = 'emotionConversion'


class EmotionConversionPlugin(BaseModel):
    schema = 'emotionConversionPlugin'


class EmotionAnalysis(BaseModel):
    schema = 'emotionAnalysis'


class EmotionModel(BaseModel):
    schema = 'emotionModel'
    onyx__hasEmotionCategory = []


class EmotionPlugin(BaseModel):
    schema = 'emotionPlugin'


class EmotionSet(BaseModel):
    schema = 'emotionSet'

    onyx__hasEmotion = []


class Evaluation(BaseModel):
    schema = 'evaluation'

    metrics = alias('senpy:metrics', [])


class Entity(BaseModel):
    schema = 'entity'


class Help(BaseModel):
    schema = 'help'


class Metric(BaseModel):
    schema = 'metric'


class Parameter(BaseModel):
    schema = 'parameter'


class Plugins(BaseModel):
    schema = 'plugins'

    plugins = []


class Response(BaseModel):
    schema = 'response'


class Results(BaseModel):
    schema = 'results'

    _terse_keys = ['entries', ]

    activities = []
    entries = []

    def activity(self, id):
        for i in self.activities:
            if i.id == id:
                return i
        return None


class SentimentPlugin(BaseModel):
    schema = 'sentimentPlugin'


class Suggestion(BaseModel):
    schema = 'suggestion'


class Topic(BaseModel):
    schema = 'topic'


class Analysis(BaseModel):
    '''
    A prov:Activity that results of executing a Plugin on an entry with a set of
    parameters.
    '''
    schema = 'analysis'

    parameters = alias('prov:used', [])
    algorithm = alias('prov:wasAssociatedWith', [])

    @property
    def params(self):
        outdict = {}
        outdict['algorithm'] = self.algorithm
        for param in self.parameters:
            outdict[param['name']] = param['value']
        return outdict

    @params.setter
    def params(self, value):
        for k, v in value.items():
            for param in self.parameters:
                if param.name == k:
                    param.value = v
                    break
            else:
                self.parameters.append(Parameter(name=k, value=v))  # noqa: F821

    def param(self, key, default=None):
        for param in self.parameters:
            if param['name'] == key:
                return param['value']
        return default

    @property
    def plugin(self):
        return self._plugin

    @plugin.setter
    def plugin(self, value):
        self._plugin = value
        self['prov:wasAssociatedWith'] = value.id

    def run(self, request):
        return self.plugin.process(request, self)


class Plugin(BaseModel):
    schema = 'plugin'
    extra_params = {}

    def activity(self, parameters=None):
        '''Generate an Analysis (prov:Activity) from this plugin and the given parameters'''
        a = Analysis()
        a.plugin = self
        if parameters:
            a.params = parameters
        return a


# More classes could be added programmatically

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
