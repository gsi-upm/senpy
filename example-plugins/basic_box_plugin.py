#!/usr/local/bin/python
# coding: utf-8

from senpy import easy_test, SentimentBox

import basic


class BasicBox(SentimentBox):
    ''' A modified version of Basic that also does converts annotations manually'''

    author = '@balkian'
    version = '0.1'

    mappings = {
        'pos': 'marl:Positive',
        'neg': 'marl:Negative',
        'default': 'marl:Neutral'
    }

    def box(self, input, **kwargs):
        output = basic.get_polarity(input)
        return self.mappings.get(output, self.mappings['default'])

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
