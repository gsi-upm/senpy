# -*- coding: utf-8 -*-

from vaderSentiment import sentiment
from senpy.plugins import SentimentBox, SenpyPlugin
from senpy.models import Results, Sentiment, Entry
import logging


class VaderSentimentPlugin(SentimentBox):
    '''
    Sentiment classifier using vaderSentiment module. Params accepted: Language: {en, es}. The output uses Marl ontology developed at GSI UPM for semantic web.
    '''
    name = "sentiment-vader"
    module = "sentiment-vader"
    author = "@icorcuera"
    version = "0.1.1"
    extra_params = {
        "language": {
          "description": "language of the input",
          "@id": "lang_rand",
          "aliases": ["language", "l"],
          "default": "auto",
          "options": ["es", "en", "auto"]
        },

        "aggregate": {
            "description": "Show only the strongest sentiment (aggregate) or all sentiments",
            "aliases": ["aggregate","agg"],
            "options": [True, False],
            "default": False
        }

    }
    requirements = {}

    _VADER_KEYS = ['pos', 'neu', 'neg']
    binary = False


    def predict_one(self, features, activity):
        text_input = ' '.join(features)
        scores = sentiment(text_input)

        sentiments = []
        for k in self._VADER_KEYS:
            sentiments.append(scores[k])

        if activity.param('aggregate'):
            m = max(sentiments)
            sentiments = [k if k==m else None for k in sentiments]

        return sentiments

    test_cases = []

    test_cases = [
        {
            'input': 'I am tired :(',
            'polarity': 'marl:Negative'
        },
        {
            'input': 'I love pizza :(',
            'polarity': 'marl:Positive'
        },
        {
            'input': 'I enjoy going to the cinema :)',
            'polarity': 'marl:Negative'
        },
        {
            'input': 'This cake is disgusting',
            'polarity': 'marl:Negative'
        },
        
    ]
