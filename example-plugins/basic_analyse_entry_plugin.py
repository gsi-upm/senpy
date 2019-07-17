#!/usr/local/bin/python
# -*- coding: utf-8 -*-
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

from senpy import easy_test, models, plugins

import basic


class BasicAnalyseEntry(plugins.SentimentPlugin):
    '''Equivalent to Basic, implementing the analyse_entry method'''

    author = '@balkian'
    version = '0.1'

    mappings = {
        'pos': 'marl:Positive',
        'neg': 'marl:Negative',
        'default': 'marl:Neutral'
    }

    def analyse_entry(self, entry, activity):
        polarity = basic.get_polarity(entry.text)

        polarity = self.mappings.get(polarity, self.mappings['default'])

        s = models.Sentiment(marl__hasPolarity=polarity)
        s.prov(activity)
        entry.sentiments.append(s)
        yield entry

    test_cases = [{
        'input': 'Hello :)',
        'polarity': 'marl:Positive'
    }, {
        'input': 'So sad :(',
        'polarity': 'marl:Negative'
    }, {
        'input': 'Yay! Emojis  😁',
        'polarity': 'marl:Positive'
    }, {
        'input': 'But no emoticons 😢',
        'polarity': 'marl:Negative'
    }]


if __name__ == '__main__':
    easy_test()
