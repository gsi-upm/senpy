class SenpyPlugin(object):
    def __init__(self, name=None, version=None, params=None):
        self.name = name
        self.version = version
        self.params = params or []

    def analyse(self, *args, **kwargs):
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass

    def jsonable(self, parameters=False):
        resp =  {
            "@id": "{}_{}".format(self.name, self.version),
        }
        if parameters:
            resp["parameters"] = self.params,
        return resp

class SentimentPlugin(SenpyPlugin):
    def __init__(self,
                 minPolarityValue=0,
                 maxPolarityValue=1,
                 **kwargs):
        super(SentimentPlugin, self).__init__(**kwargs)
        self.minPolarityValue = minPolarityValue
        self.maxPolarityValue = maxPolarityValue

    def jsonable(self, *args, **kwargs):
        resp = super(SentimentPlugin, self).jsonable(*args, **kwargs)
        resp["marl:maxPolarityValue"] = self.maxPolarityValue
        resp["marl:minPolarityValue"] = self.minPolarityValue
        return resp

class EmotionPlugin(SenpyPlugin):
    def __init__(self,
                 minEmotionValue=0,
                 maxEmotionValue=1,
                 emotionCategory=None,
                 **kwargs):
        super(EmotionPlugin, self).__init__(**kwargs)
        self.minEmotionValue = minEmotionValue
        self.maxEmotionValue = maxEmotionValue
        self.emotionCategory = emotionCategory

    def jsonable(self, *args, **kwargs):
        resp = super(EmotionPlugin, self).jsonable(*args, **kwargs)
        resp["onyx:minEmotionValue"] = self.minEmotionValue
        resp["onyx:maxEmotionValue"] = self.maxEmotionValue
        return resp
