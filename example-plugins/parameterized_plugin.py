#!/usr/local/bin/python
# -*- coding: utf-8 -*-

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
