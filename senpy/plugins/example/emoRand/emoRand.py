import random

from senpy.plugins import EmotionPlugin
from senpy.models import EmotionSet, Emotion


class RmoRandPlugin(EmotionPlugin):
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
