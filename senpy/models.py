import json
import os
from collections import defaultdict
from pyld import jsonld



class Leaf(dict):
    _prefix = None
    _frame = {}
    _context = {}

    def __init__(self,
                 id=None,
                 context=None,
                 vocab=None,
                 prefix=None,
                 frame=None):
        super(Leaf, self).__init__()
        if context is not None:
            self.context = context
        elif self._context:
            self.context = self._context
        else:
            self.context = {}
        if frame is not None:
            self._frame = frame
        self._prefix = prefix
        self.id = id

    def __getattr__(self, key):
        try:
            return object.__getattr__(self, key)
        except AttributeError:
            try:
                return super(Leaf, self).__getitem__(self._get_key(key))
            except KeyError:
                raise AttributeError()

    def __setattr__(self, key, value):
        try:
            object.__getattr__(self, key)
            object.__setattr__(self, key, value)
        except AttributeError:
            key = self._get_key(key)
            if key == "@context":
                value = self.get_context(value)
            elif key == "@id":
                value = self.get_id(value)
            if key[0] == "_":
                object.__setattr__(self, key, value)
            else:
                if value is None:
                    try:
                        super(Leaf, self).__delitem__(key)
                    except KeyError:
                        pass
                else:
                    super(Leaf, self).__setitem__(key, value)

    def get_id(self, id):
        """
        This is not the most elegant solution to change the @id attribute, but it
        is the quickest way to have it included in the dictionary without extra
        boilerplate.
        """
        if id and self._prefix and ":" not in id:
            return "{}{}".format(self._prefix, id)
        else:
            return id

    def __delattr__(self, key):
        return super(Leaf, self).__delitem__(self._get_key(key))

    def _get_key(self, key):
        if key[0] == "_":
            return key
        elif key in ["context", "id"]:
            return "@{}".format(key)
        else:
            return key

    @staticmethod
    def get_context(context):
        if isinstance(context, list):
            contexts = []
            for c in context:
                contexts.append(Response.get_context(c))
            return contexts
        elif isinstance(context, dict):
            return context
        elif isinstance(context, basestring):
            try:
                with open(context) as f:
                    return json.loads(f.read())
            except IOError:
                return context

    def compact(self):
        return jsonld.compact(self, self.context)

    def frame(self, frame=None, options=None):
        if frame is None:
            frame = self._frame
        if options is None:
            options = {}
        return jsonld.frame(self, frame, options)

    def jsonable(self, parameters=False, frame=None, options=None, context=None):
        if frame is None:
            frame = self._frame
        if options is None:
            options = {}
        if context is None:
            context = self._context
        return jsonld.compact(jsonld.frame(self, frame, options), context)
        #if parameters:
            #resp["parameters"] = self.params
        #elif self.extra_params:
            #resp["extra_parameters"] = self.extra_params
        #return resp


    def to_JSON(self):
        return json.dumps(self,
                          default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)



class Response(Leaf):
    _frame =  { "@context": {
                    "analysis": {
                        "@container": "@set",
                        "@id": "prov:wasInformedBy"
                    },
                    "date": {
                        "@id": "dc:date",
                        "@type": "xsd:dateTime"
                    },
                    "dc": "http://purl.org/dc/terms/",
                    "dc:subject": {
                        "@type": "@id"
                    },
                    "emotions": {
                        "@container": "@set",
                        "@id": "onyx:hasEmotionSet"
                    },
                    "entries": {
                        "@container": "@set",
                        "@id": "prov:generated"
                    },
                    "marl": "http://www.gsi.dit.upm.es/ontologies/marl/ns#",
                    "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#",
                    "onyx": "http://www.gsi.dit.upm.es/ontologies/onyx/ns#",
                    "opinions": {
                        "@container": "@set",
                        "@id": "marl:hasOpinion"
                    },
                    "prov": "http://www.w3.org/ns/prov#",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
                    "strings": {
                        "@container": "@set",
                        "@reverse": "nif:hasContext"
                    },
                    "wnaffect": "http://www.gsi.dit.upm.es/ontologies/wnaffect#",
                    "xsd": "http://www.w3.org/2001/XMLSchema#"
                },
                "analysis": {},
                "entries": {}
    }

    def __init__(self, context=None, *args, **kwargs):
        if context is None:
            context = "{}/context.jsonld".format(os.path.dirname(
                os.path.realpath(__file__)))
        super(Response, self).__init__(*args, context=context, **kwargs)
        self.analysis = []
        self.entries = []


class Entry(Leaf):
    _context = {
        "@vocab": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"

    }
    def __init__(self, text=None, emotion_sets=None, opinions=None, **kwargs):
        super(Entry, self).__init__(**kwargs)
        if text:
            self.text = text
        self.emotionSets = emotion_sets if emotion_sets else []
        self.opinions = opinions if opinions else []

class Opinion(Leaf):
    _context = {
        "@vocab": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"
    }
    def __init__(self, polarityValue=None, hasPolarity=None, *args, **kwargs):
        super(Opinion, self).__init__(*args,
                                      **kwargs)
        if polarityValue is not None:
            self.hasPolarityValue = polarityValue
        if hasPolarity is not None:
            self.hasPolarity = hasPolarity


class EmotionSet(Leaf):
    _context = {}
    def __init__(self, emotions=None, *args, **kwargs):
        if not emotions:
            emotions = []
        super(EmotionSet, self).__init__(context=EmotionSet._context,
                                         *args,
                                         **kwargs)
        self.emotions = emotions or []

class Emotion(Leaf):
    _context = {}

class Error(Leaf):
    def __init__(self, *args, **kwargs):
        super(Error, self).__init__(*args)
        self.update(kwargs)
