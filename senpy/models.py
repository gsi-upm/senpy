import json
import os
from collections import defaultdict

class Leaf(defaultdict):
    def __init__(self, ofclass=list):
        super(Leaf, self).__init__(ofclass)

    def __getattr__(self, name):
        return super(Leaf, self).__getitem__(name)

    def __setattr__(self, name, value):
        self[name] = value

    def __delattr__(self, name):
        return super(Leaf, self).__delitem__(name)

class Response(Leaf):
    def __init__(self, context=None):
        super(Response, self).__init__()
        self["analysis"] = []
        self["entries"] = []
        if context is None:
            context = "{}/context.jsonld".format(os.path.dirname(
                                                 os.path.realpath(__file__)))
        if isinstance(context, dict):
            self["@context"] = context
        if isinstance(context, basestring):
            try:
                with open(context) as f:
                    self["@context"] = json.loads(f.read())
            except IOError:
                self["@context"] = context


class Entry(Leaf):
    def __init__(self, text=None, emotionSets=None, opinions=None, **kwargs):
        super(Entry, self).__init__(**kwargs)
        if text:
            self.text = text
        if emotionSets:
            self.emotionSets = emotionSets
        if opinions:
            self.opinions = opinions

class Opinion(Leaf):
    def __init__(self, polarityValue=None, polarity=None, **kwargs):
        super(Opinion, self).__init__(**kwargs)
        if polarityValue is not None:
            self.polarityValue = polarityValue
        if polarity is not None:
            self.polarity = polarity



class EmotionSet(Leaf):
    def __init__(self, emotions=[], **kwargs):
        super(EmotionSet, self).__init__(**kwargs)
        self.emotions = emotions or []
