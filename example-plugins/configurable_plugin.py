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


class Dictionary(plugins.SentimentPlugin):
    '''Sentiment annotation using a configurable lexicon'''

    author = '@balkian'
    version = '0.2'

    dictionaries = [basic.emojis, basic.emoticons]

    mappings = {'pos': 'marl:Positive', 'neg': 'marl:Negative'}

    def analyse_entry(self, entry, *args, **kwargs):
        polarity = basic.get_polarity(entry.text, self.dictionaries)
        if polarity in self.mappings:
            polarity = self.mappings[polarity]

        s = models.Sentiment(marl__hasPolarity=polarity)
        s.prov(self)
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


class EmojiOnly(Dictionary):
    '''Sentiment annotation with a basic lexicon of emojis'''
    dictionaries = [basic.emojis]

    test_cases = [{
        'input': 'Hello :)',
        'polarity': 'marl:Neutral'
    }, {
        'input': 'So sad :(',
        'polarity': 'marl:Neutral'
    }, {
        'input': 'Yay! Emojis  😁',
        'polarity': 'marl:Positive'
    }, {
        'input': 'But no emoticons 😢',
        'polarity': 'marl:Negative'
    }]


class EmoticonsOnly(Dictionary):
    '''Sentiment annotation with a basic lexicon of emoticons'''
    dictionaries = [basic.emoticons]

    test_cases = [{
        'input': 'Hello :)',
        'polarity': 'marl:Positive'
    }, {
        'input': 'So sad :(',
        'polarity': 'marl:Negative'
    }, {
        'input': 'Yay! Emojis  😁',
        'polarity': 'marl:Neutral'
    }, {
        'input': 'But no emoticons 😢',
        'polarity': 'marl:Neutral'
    }]


class Salutes(Dictionary):
    '''Sentiment annotation with a custom lexicon, for illustration purposes'''
    dictionaries = [{
        'marl:Positive': ['Hello', '!'],
        'marl:Negative': ['Good bye', ]
    }]

    test_cases = [{
        'input': 'Hello :)',
        'polarity': 'marl:Positive'
    }, {
        'input': 'Good bye :(',
        'polarity': 'marl:Negative'
    }, {
        'input': 'Yay! Emojis  😁',
        'polarity': 'marl:Positive'
    }, {
        'input': 'But no emoticons 😢',
        'polarity': 'marl:Neutral'
    }]


if __name__ == '__main__':
    easy_test()
