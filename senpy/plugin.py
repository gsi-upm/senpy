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

class SentimentPlugin(SenpyPlugin):
    def __init__(self,
                 minPolarity=0,
                 maxPolarity=1,
                 **kwargs):
        super(SentimentPlugin, self).__init__(**kwargs)
        self.minPolarity = minPolarity
        self.maxPolarity = maxPolarity

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
