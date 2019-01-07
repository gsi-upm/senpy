#!/usr/local/bin/python
# -*- coding: utf-8 -*-

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
