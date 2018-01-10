#!/usr/local/bin/python
# coding: utf-8

from senpy import easy_test, SentimentBox, MappingMixin

import basic


class Basic(MappingMixin, SentimentBox):
    '''Provides sentiment annotation using a lexicon'''

    author = '@balkian'
    version = '0.1'

    mappings = {
        'pos': 'marl:Positive',
        'neg': 'marl:Negative',
        'default': 'marl:Neutral'
    }

    def predict(self, input):
        return basic.get_polarity(input)

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
