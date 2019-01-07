#!/usr/local/bin/python
# -*- coding: utf-8 -*-

from senpy import easy_test, SentimentBox

import basic


class BasicBox(SentimentBox):
    ''' A modified version of Basic that also does converts annotations manually'''

    author = '@balkian'
    version = '0.1'

    def predict_one(self, features, **kwargs):
        output = basic.get_polarity(features[0])
        if output == 'pos':
            return [1, 0, 0]
        if output == 'neg':
            return [0, 0, 1]
        return [0, 1, 0]

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
