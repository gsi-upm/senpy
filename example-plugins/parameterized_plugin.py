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


class ParameterizedDictionary(plugins.SentimentPlugin):
    '''This is a basic self-contained plugin'''

    author = '@balkian'
    version = '0.2'

    extra_params = {
        'positive-words': {
            'description': 'Comma-separated list of words that are considered positive',
            'aliases': ['positive'],
            'required': True
        },
        'negative-words': {
            'description': 'Comma-separated list of words that are considered negative',
            'aliases': ['negative'],
            'required': False
        }
    }

    def analyse_entry(self, entry, activity):
        params = activity.params
        positive_words = params['positive-words'].split(',')
        negative_words = params['negative-words'].split(',')
        dictionary = {
            'marl:Positive': positive_words,
            'marl:Negative': negative_words,
        }
        polarity = basic.get_polarity(entry.text, [dictionary])

        s = models.Sentiment(marl__hasPolarity=polarity)
        s.prov(activity)
        entry.sentiments.append(s)
        yield entry

    test_cases = [
        {
            'input': 'Hello :)',
            'polarity': 'marl:Positive',
            'parameters': {
                'positive': "Hello,:)",
                'negative': "sad,:()"
            }
        },
        {
            'input': 'Hello :)',
            'polarity': 'marl:Negative',
            'parameters': {
                'positive': "",
                'negative': "Hello"
            }
        }
    ]


if __name__ == '__main__':
    easy_test()
