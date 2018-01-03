import random

from senpy.plugins import EmotionPlugin
from senpy.models import EmotionSet, Emotion, Entry


class EmoRand(EmotionPlugin):
    '''A sample plugin that returns a random emotion annotation'''
    author = '@balkian'
    version = '0.1'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    onyx__usesEmotionModel = "emoml:big6"

    def analyse_entry(self, entry, params):
        category = "emoml:big6happiness"
        number = max(-1, min(1, random.gauss(0, 0.5)))
        if number > 0:
            category = "emoml:big6anger"
        emotionSet = EmotionSet()
        emotion = Emotion({"onyx:hasEmotionCategory": category})
        emotionSet.onyx__hasEmotion.append(emotion)
        emotionSet.prov__wasGeneratedBy = self.id
        entry.emotions.append(emotionSet)
        yield entry

    def test(self):
        params = dict()
        results = list()
        for i in range(100):
            res = next(self.analyse_entry(Entry(nif__isString="Hello"), params))
            res.validate()
            results.append(res.emotions[0]['onyx:hasEmotion'][0]['onyx:hasEmotionCategory'])
