import json
import os
from collections import defaultdict
from pyld import jsonld
import logging
from flask import Response as FlaskResponse


class Leaf(dict):
    _prefix = None
    _frame = {}
    _context = {}

    def __init__(self,
                 *args,
                 **kwargs):

        id = kwargs.pop("id", None)
        context = kwargs.pop("context", self._context)
        vocab = kwargs.pop("vocab", None)
        prefix = kwargs.pop("prefix", None)
        frame = kwargs.pop("frame", None)
        super(Leaf, self).__init__(*args, **kwargs)
        if context is not None:
            self.context = context
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
        Get id, dealing with prefixes
        """
        # This is not the most elegant solution to change the @id attribute,
        # but it is the quickest way to have it included in the dictionary
        # without extra boilerplate.
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
        return jsonld.compact(self, self.get_context(self.context))

    def frame(self, frame=None, options=None):
        if frame is None:
            frame = self._frame
        if options is None:
            options = {}
        return jsonld.frame(self, frame, options)

    def jsonld(self, frame=None, options=None,
               context=None, removeContext=None):
        if removeContext is None:
            removeContext = Response._context  # Loop?
        if frame is None:
            frame = self._frame
        if context is None:
            context = self.context
        else:
            context = self.get_context(context)
        # For some reason, this causes errors with pyld
        # if options is None:
            # options = {"expandContext": context.copy() }
        js = self
        if frame:
            logging.debug("Framing: %s", json.dumps(self, indent=4))
            logging.debug("Framing with %s", json.dumps(frame, indent=4))
            js = jsonld.frame(js, frame, options)
            logging.debug("Result: %s", json.dumps(js, indent=4))
            logging.debug("Compacting with %s", json.dumps(context, indent=4))
            js = jsonld.compact(js, context, options)
            logging.debug("Result: %s", json.dumps(js, indent=4))
        if removeContext == context:
            del js["@context"]
        return js

    def to_JSON(self, removeContext=None):
        return json.dumps(self.jsonld(removeContext=removeContext),
                          default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    def flask(self,
              in_headers=False,
              url="http://demos.gsi.dit.upm.es/senpy/senpy.jsonld"):
        """
        Return the values and error to be used in flask
        """
        js = self.jsonld()
        headers = None
        if in_headers:
            ctx = js["@context"]
            headers = {
                "Link": ('<%s>;'
                         'rel="http://www.w3.org/ns/json-ld#context";'
                         ' type="application/ld+json"' % url)
            }
            del js["@context"]
        return FlaskResponse(json.dumps(js, indent=4),
                             status=self.get("status", 200),
                             headers=headers,
                             mimetype="application/json")


class Response(Leaf):
    _context = Leaf.get_context("{}/context.jsonld".format(
        os.path.dirname(os.path.realpath(__file__))))
    _frame = {
        "@context": _context,
        "analysis": {
            "@explicit": True,
            "maxPolarityValue": {},
            "minPolarityValue": {},
            "name": {},
            "version": {},
        },
        "entries": {}
    }

    def __init__(self, *args, **kwargs):
        context = kwargs.pop("context", None)
        frame = kwargs.pop("frame", None)
        if context is None:
            context = self._context
        self.context = context
        super(Response, self).__init__(
            *args, context=context, frame=frame, **kwargs)
        if self._frame is not None and "entries" in self._frame:
            self.analysis = []
            self.entries = []

    def jsonld(self, frame=None, options=None, context=None, removeContext={}):
        return super(Response, self).jsonld(frame,
                                            options,
                                            context,
                                            removeContext)


class Entry(Leaf):
    _context = {
        "@vocab": ("http://persistence.uni-leipzig.org/"
                   "nlp2rdf/ontologies/nif-core#")

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
    # A better pattern would be this:
    # http://flask.pocoo.org/docs/0.10/patterns/apierrors/
    _frame = {}
    _context = {}

    def __init__(self, *args, **kwargs):
        super(Error, self).__init__(*args, **kwargs)
