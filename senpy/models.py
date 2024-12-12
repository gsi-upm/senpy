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
'''


from typing import *

import os
import logging
import jmespath
import json

from textwrap import dedent

from pydantic import BaseModel as PydanticModel
from pydantic import computed_field, field_validator, ConfigDict, Field
from pydantic_core import from_json

logging.getLogger('rdflib').setLevel(logging.WARN)
logger = logging.getLogger(__name__)


CONTEXT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                            'schemas',
                            'context.jsonld')

with open(CONTEXT_PATH) as f:
    BASE_CONTEXT = dict(json.loads(f.read()))


class BaseModel(PydanticModel):
    '''
    Entities of the base model are a special kind of dictionary that emulates
    a JSON-LD object.
    The basic attributes should be set in the class, but additional values can 
    also be provided/set via attributes (à la Javascript). e.g.:

    >>> myobject.key == myobject['key']
    True
    >>> myobject['ns:name'] = 'Peter'
    True
    '''
    model_config = ConfigDict(extra='ignore', ignored_types=(object, ))
    context: Optional[Union[str, Dict]] = Field(default=None, serialization_alias="@context")
    wasGeneratedBy: Optional[str] = Field(default=None, serialization_alias="prov:wasGeneratedBy")

    @property
    def id(self):
        if '@id' not in self:
            self['@id'] = 'prefix:{}_{}'.format(type(self).__name__, time.time())
        return self['@id']

    @id.setter
    def id(self, value):
        self['@id'] = value

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
                        self.context,
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


class Entry(BaseModel):
    text: str = Field(serialization_alias="nif:isString")

class Activity(BaseModel):
    plugin: str
    params: Dict[str, Any]
    analyzed: List[str] = []


class Results(BaseModel):
    activities: List[Activity] = []
    entries: List[Entry] = []
    parameters: Dict[str, str] = {}


class Analysis(BaseModel):
    plugin: 'Plugin'
    params: dict[str, object] = {}

    def run(self, request):
        return self.plugin.process(request, self)


class MoralityAnalysis(Analysis):
    usedMoralValueModel: str
    usedMLModel: Optional[str] = None


class Annotation(BaseModel):
    annotated: Optional[str] = None
    wasGeneratedBy: Optional[str] = None

    def add_provenance(self, entry, activity):
        self.annotated = entry.id
        self.wasGeneratedBy = activity.id
        self[prov['wasGeneratedBy']] = activity.id
        activity.analysed.append(entry.id)


class MoralAnnotation(Annotation):
    def __init__(self, category, confidence=None, intensity=None,
                 entry=None, activity=None):
        super().__init__()
        if confidence is not None:
            self[amor['confidence']] = confidence
        if intensity is not None:
            self[amor_mft['hasPolarityIntensity']] = intensity
        if entry and activity:
             self.add_provenance(entry, activity)
        elif entry or activity:
            raise Exception()

    @classmethod
    def from_label(cls, label):
        return cls(label.category, label.confidence, label.intensity)


class Plugin(BaseModel):
    name: str = Field(default='', validate_default=True)
    version: Optional[str] = 'dev'
    author: Optional[str] = None
    extra_params: Dict[str, Any] = {}
    description: str = Field(default="", json_schema_extra=dict(hidden=True))

    @field_validator("description", mode="before")
    @classmethod
    def dedentdoc(cls, doc: str) -> str:
        doc = doc or cls.get('__doc__', None)
        return dedent(doc)

    @field_validator("name", mode="before")
    @classmethod
    def clsname(cls, name: str) -> str:
        name = name or cls.__name__.capitalize()
        return name

    @computed_field
    @property
    def id(self) -> str:
        return 'endpoint:plugins/{}_{}'.format(self.name, self.version)

    def activity(self, params, *, cls=Analysis):
        '''Generate an Analysis (prov:Activity) from this plugin and the given parameters'''
        a = cls(plugin=self, params=params)
        return a
 

class Plugins(BaseModel):
    plugins: List[Plugin] = []

class Emotion:
    hasEmotionIntensity: str = Field(serialization_alias="onyx:hasEmotionIntensity")
    hasEmotionCategory: str = Field(serialization_alias="onyx:hasEmotionCategory")

class Sentiment:
    pass

class SentimentPlugin(Plugin):
    pass

class Suggestion:
    pass

class Topic:
    pass


class Context:
    pass

class Dataset:
    pass

class Datasets:
    pass

class Definitions:
    pass

class Dimensions:
    pass

class EmotionAnalysis:
    pass

class EmotionConversion:
    pass

class EmotionConversionPlugin(Plugin):
    pass

class Emotion:
    pass

class EmotionModel:
    pass

class EmotionPlugin(Plugin):
    pass

class EmotionSet:
    pass

class Entity:
    pass

class ErrorResponse(BaseModel):
    code: Optional[int] = 500
    message: str


class Metric:
    pass

class Evaluation:
    pass

class AggregatedEvaluation:
    pass

class Help:
    pass

class Parameter:
    pass



def from_dict(c, cls):
    return cls.model_validate(d)


def from_string(s, cls):
    return from_dict(from_json(s, allow_partial=True))
