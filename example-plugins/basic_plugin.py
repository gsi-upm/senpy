#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from senpy import easy_test, SentimentBox

import basic


class Basic(SentimentBox):
    '''Provides sentiment annotation using a lexicon'''

    author = '@balkian'
    version = '0.1'

    def predict_one(self, features, **kwargs):
        output = basic.get_polarity(features[0])
        if output == 'pos':
            return [1, 0, 0]
        if output == 'neu':
            return [0, 1, 0]
        return [0, 0, 1]

    test_cases = [{
        'input': u'Hello :)',
        'polarity': 'marl:Positive'
    }, {
        'input': u'So sad :(',
        'polarity': 'marl:Negative'
    }, {
        'input': u'Yay! Emojis  😁',
        'polarity': 'marl:Positive'
    }, {
        'input': u'But no emoticons 😢',
        'polarity': 'marl:Negative'
    }]


if __name__ == '__main__':
    easy_test()
