'''
Senpy Models. 

This implementation should mirror the JSON schema definition.
For compatibility with Py3 and for easier debugging, this new version drops introspection
and adds all arguments to the models.
'''
from __future__ import print_function
from six import string_types

import time
import copy
import json
import os
import logging
import jsonref
import jsonschema

from flask import Response as FlaskResponse


DEFINITIONS_FILE = 'definitions.json'
CONTEXT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schemas', 'context.jsonld')

def get_schema_path(schema_file, absolute=False):
    if absolute:
        return os.path.realpath(schema_file)
    else:
        return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'schemas', schema_file)


def read_schema(schema_file, absolute=False):
    schema_path = get_schema_path(schema_file, absolute)
    schema_uri = 'file://{}'.format(schema_path)
    return jsonref.load(open(schema_path), base_uri=schema_uri)
        

base_schema = read_schema(DEFINITIONS_FILE)
logging.debug(base_schema)

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
    context = base_context

    def flask(self,
              in_headers=False,
              url="http://demos.gsi.dit.upm.es/senpy/senpy.jsonld"):
        """
        Return the values and error to be used in flask
        """
        headers = None
        if in_headers:
            headers = {
                "Link": ('<%s>;'
                         'rel="http://www.w3.org/ns/json-ld#context";'
                         ' type="application/ld+json"' % url)
            }
        return FlaskResponse(self.to_JSON(with_context=not in_headers),
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


    def jsonld(self, context=None, with_context=False):
        ser = self.serializable()

        if  with_context:
            ser["@context"] = self.context

        return ser


    def to_JSON(self, *args, **kwargs):
        js = json.dumps(self.jsonld(*args, **kwargs), indent=4,
                        sort_keys=True)
        return js

    def validate(self, obj=None):
        if not obj:
            obj = self
        if hasattr(obj, "jsonld"):
            obj = obj.jsonld()
        jsonschema.validate(obj, self.schema)
    
class SenpyModel(SenpyMixin, dict):

    schema = base_schema

    def __init__(self, *args, **kwargs):
        temp = dict(*args, **kwargs)

        reqs = self.schema.get('required', [])
        for i in reqs:
            if i not in temp:
                prop = self.schema['properties'][i]
                if 'default' in prop:
                    temp[i] = copy.deepcopy(prop['default'])
        if 'context' in temp:
            context = temp['context']
            del temp['context']
            self.__dict__['context'] = Context.load(context)
        super(SenpyModel, self).__init__(temp)


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
        
    
    @classmethod
    def from_base(cls, name):
        subschema = base_schema[name]
        return warlock.model_factory(subschema, base_class=cls)

    def _plain_dict(self):
        d =  { k: v for (k,v) in self.items() if k[0] != "_"}
        if hasattr(self, "id"):
            d["@id"] = self.id
        return d

    @property
    def id(self):
        if not hasattr(self, '_id'):
            self.__dict__["_id"] = '_:{}_{}'.format(type(self).__name__, time.time())
        return self._id

    @id.setter
    def id(self, value):
        self._id = value
    

class Response(SenpyModel):
    schema = read_schema('response.json')

class Results(SenpyModel):
    schema = read_schema('results.json')

    def jsonld(self, context=None, with_context=True):
        return super(Results, self).jsonld(context, with_context)

class Entry(SenpyModel):
    schema = read_schema('entry.json')

class Sentiment(SenpyModel):
    schema = read_schema('sentiment.json')

class Analysis(SenpyModel):
    schema = read_schema('analysis.json')

class EmotionSet(SenpyModel):
    schema = read_schema('emotionSet.json')

class Suggestion(SenpyModel):
    schema = read_schema('suggestion.json')

class PluginModel(SenpyModel):
    schema = read_schema('plugin.json')

class Plugins(SenpyModel):
    schema = read_schema('plugins.json')

class Error(SenpyMixin, BaseException ):

    def __init__(self, message, status=500, params=None, errors=None, *args, **kwargs):
        self.message = message
        self.status = status
        self.params = params or {}
        self.errors = errors or ""

    def _plain_dict(self):
       return self.__dict__

    def __str__(self):
       return str(self.jsonld()) 
