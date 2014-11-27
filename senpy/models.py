import json
import os
from collections import defaultdict


class Leaf(defaultdict):
    def __init__(self, context=None, ofclass=list):
        super(Leaf, self).__init__(ofclass)
        if context:
            self.context = context

    def __getattr__(self, name):
        if name is not "context":
            return super(Leaf, self).__getitem__(name)
        return self["@context"]

    def __setattr__(self, name, value):
        name = "@context" if name is "context" else name
        self[name] = self.get_context(value)

    def __delattr__(self, name):
        return super(Leaf, self).__delitem__(name)

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
    def __init__(self, context=None, *args, **kwargs):
        if context is None:
            context = "{}/context.jsonld".format(os.path.dirname(
                os.path.realpath(__file__)))
        super(Response, self).__init__(*args, context=context, **kwargs)
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
    opinionContext = {
        "@vocab": "http://www.gsi.dit.upm.es/ontologies/marl/ns#"
    }
    def __init__(self, polarityValue=None, hasPolarity=None, *args, **kwargs):
        super(Opinion, self).__init__(context=self.opinionContext,
                                      *args,
                                      **kwargs)
        if polarityValue is not None:
            self.polarityValue = polarityValue
        if hasPolarity is not None:
            self.hasPolarity = hasPolarity


class EmotionSet(Leaf):
    emotionContext = {
        "@vocab": "http://www.gsi.dit.upm.es/ontologies/onyx/ns#"
    }
    def __init__(self, emotions=None, *args, **kwargs):
        if not emotions:
            emotions = []
        super(EmotionSet, self).__init__(context=self.emotionContext,
                                         *args,
                                         **kwargs)
        self.emotions = emotions or []
