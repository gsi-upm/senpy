import json
import os
from collections import defaultdict


class Leaf(defaultdict):
    _prefix = None

    def __init__(self, id=None, context=None, prefix=None, ofclass=list):
        super(Leaf, self).__init__(ofclass)
        if context:
            self.context = context
        if id:
            self.id = id
        self._prefix = prefix

    def __getattr__(self, key):
        return super(Leaf, self).__getitem__(self._get_key(key))

    def __setattr__(self, key, value):
        try:
            object.__getattr__(self, key)
            object.__setattr__(self, key, value)
        except AttributeError:
            key = self._get_key(key)
            value = self.get_context(value) if key == "@context" else value
            if key[0] == "_":
                object.__setattr__(self, key, value)
            else:
                super(Leaf, self).__setitem__(key, value)

    def __delattr__(self, key):
        return super(Leaf, self).__delitem__(self._get_key(key))

    def _get_key(self, key):
        if key in ["context", "id"]:
            return "@{}".format(key)
        elif self._prefix:
            return "{}:{}".format(self._prefix, key)
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


class Response(Leaf):
    def __init__(self, context=None, base=None, *args, **kwargs):
        if context is None:
            context = "{}/context.jsonld".format(os.path.dirname(
                os.path.realpath(__file__)))
        super(Response, self).__init__(*args, context=context, **kwargs)
        if base:
            self.context["@base"] = base
        self["analysis"] = []
        self["entries"] = []


class Entry(Leaf):
    def __init__(self, text=None, emotion_sets=None, opinions=None, **kwargs):
        super(Entry, self).__init__(**kwargs)
        if text:
            self.text = text
        if emotion_sets:
            self.emotionSets = emotion_sets
        if opinions:
            self.opinions = opinions


class Opinion(Leaf):
    #opinionContext = {"@vocab": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"}
    def __init__(self, polarityValue=None, hasPolarity=None, *args, **kwargs):
        super(Opinion, self).__init__( prefix="marl",
                                      *args,
                                      **kwargs)
        if polarityValue is not None:
            self.polarityValue = polarityValue
        if hasPolarity is not None:
            self.hasPolarity = hasPolarity


class EmotionSet(Leaf):
    emotionContext = {}
    def __init__(self, emotions=None, *args, **kwargs):
        if not emotions:
            emotions = []
        super(EmotionSet, self).__init__(context=EmotionSet.emotionContext,
                                         *args,
                                         **kwargs)
        self.emotions = emotions or []

class Emotion(Leaf):
    emotionContext = {}
    def __init__(self, emotions=None, *args, **kwargs):
        super(EmotionSet, self).__init__(context=Emotion.emotionContext,
                                         *args,
                                         **kwargs)
