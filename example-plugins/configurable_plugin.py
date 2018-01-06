#!/usr/local/bin/python
# coding: utf-8

from senpy import easy_test, models, plugins

import basic


class Dictionary(plugins.SentimentPlugin):
    '''Sentiment annotation using a configurable lexicon'''

    author = '@balkian'
    version = '0.2'

    dictionaries = [basic.emojis, basic.emoticons]

    mappings = {'pos': 'marl:Positive', 'neg': 'marl:Negative'}

    def analyse_entry(self, entry, params):
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
    description = 'A plugin'
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
