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
    context = base_context["@context"]

    def flask(self,
              in_headers=False,
              headers=None,
              **kwargs):
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
        return FlaskResponse(json.dumps(js, indent=2, sort_keys=True),
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

        if  with_context:
            context = []
            if context_uri:
                context = context_uri
            else:
                context = self.context.copy()
            if hasattr(self, 'prefix'):
                # This sets @base for the document, which will be used in
                # all relative URIs will. For example, if a uri is "Example" and
                # prefix =s "http://example.com", the absolute URI after expanding
                # with JSON-LD will be "http://example.com/Example"

                prefix_context = {"@base": self.prefix}
                if isinstance(context, list):
                    context.append(prefix_context)
                else:
                    context = [context, prefix_context]
            ser["@context"] = context
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
        self.id = kwargs.pop('id', '{}_{}'.format(type(self).__name__,
                                                    time.time()))

        temp = dict(*args, **kwargs)

        for i in temp:
            nk = self._get_key(i)
            if nk != i:
                temp[nk] = temp[i]
                del temp[i]

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
        
    
    def _plain_dict(self):
        d =  { k: v for (k,v) in self.items() if k[0] != "_"}
        d["@id"] = d.pop('id')
        return d

class Response(SenpyModel):
    schema = read_schema('response.json')

class Results(SenpyModel):
    schema = read_schema('results.json')

class Entry(SenpyModel):
    schema = read_schema('entry.json')

class Sentiment(SenpyModel):
    schema = read_schema('sentiment.json')

class Analysis(SenpyModel):
    schema = read_schema('analysis.json')

class EmotionSet(SenpyModel):
    schema = read_schema('emotionSet.json')

class Emotion(SenpyModel):
    schema = read_schema('emotion.json')

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
