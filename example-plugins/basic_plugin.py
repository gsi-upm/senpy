#!/usr/local/bin/python
# coding: utf-8

from senpy import easy_test, models, plugins

import basic


class Basic(plugins.SentimentPlugin):
    '''Provides sentiment annotation using a lexicon'''

    author = '@balkian'
    version = '0.1'

    def analyse_entry(self, entry, params):

        polarity = basic.get_polarity(entry.text)

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


if __name__ == '__main__':
    easy_test()
