#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

import random

from senpy.plugins import EmotionPlugin
from senpy.models import EmotionSet, Emotion, Entry


class EmoRand(EmotionPlugin):
    '''A sample plugin that returns a random emotion annotation'''
    name = 'emotion-random'
    author = '@balkian'
    version = '0.1'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    onyx__usesEmotionModel = "emoml:big6"

    def analyse_entry(self, entry, activity):
        category = "emoml:big6happiness"
        number = max(-1, min(1, random.gauss(0, 0.5)))
        if number > 0:
            category = "emoml:big6anger"
        emotionSet = EmotionSet()
        emotion = Emotion({"onyx:hasEmotionCategory": category})
        emotionSet.onyx__hasEmotion.append(emotion)
        emotionSet.prov(activity)
        entry.emotions.append(emotionSet)
        yield entry

    def test(self):
        params = dict()
        results = list()
        for i in range(100):
            res = next(self.analyse_entry(Entry(nif__isString="Hello"), self.activity(params)))
            res.validate()
            results.append(res.emotions[0]['onyx:hasEmotion'][0]['onyx:hasEmotionCategory'])
