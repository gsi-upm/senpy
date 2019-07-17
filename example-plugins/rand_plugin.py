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
from senpy import SentimentPlugin, Sentiment, Entry


class RandSent(SentimentPlugin):
    '''A sample plugin that returns a random sentiment annotation'''
    name = 'sentiment-random'
    author = "@balkian"
    version = '0.1'
    url = "https://github.com/gsi-upm/senpy-plugins-community"
    marl__maxPolarityValue = '1'
    marl__minPolarityValue = "-1"

    def analyse_entry(self, entry, activity):
        polarity_value = max(-1, min(1, random.gauss(0.2, 0.2)))
        polarity = "marl:Neutral"
        if polarity_value > 0:
            polarity = "marl:Positive"
        elif polarity_value < 0:
            polarity = "marl:Negative"
        sentiment = Sentiment(marl__hasPolarity=polarity,
                              marl__polarityValue=polarity_value)
        sentiment.prov(activity)
        entry.sentiments.append(sentiment)
        yield entry

    def test(self):
        '''Run several random analyses.'''
        params = dict()
        results = list()
        for i in range(50):
            activity = self.activity(params)
            res = next(self.analyse_entry(Entry(nif__isString="Hello"),
                                          activity))
            res.validate()
            results.append(res.sentiments[0]['marl:hasPolarity'])
        assert 'marl:Positive' in results
        assert 'marl:Negative' in results
