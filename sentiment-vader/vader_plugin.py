# -*- coding: utf-8 -*-

from vaderSentiment import sentiment
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Sentiment, Entry
import logging


class VaderSentimentPlugin(SentimentPlugin):
    '''
    Sentiment classifier using vaderSentiment module. Params accepted: Language: {en, es}. The output uses Marl ontology developed at GSI UPM for semantic web.
    '''
    name = "sentiment-vader"
    module = "sentiment-vader"
    author = "@icorcuera"
    version = "0.1.1"
    extra_params = {
        "language": {
          "@id": "lang_rand",
          "aliases": ["language", "l"],
          "default": "auto",
          "options": ["es", "en", "auto"]
        },

        "aggregate": {
            "aliases": ["aggregate","agg"],
            "options": ["true", "false"],
            "default": False
        }

    }
    requirements = {}

    def analyse_entry(self, entry, params):

        self.log.debug("Analysing with params {}".format(params))

        text_input = entry.text
        aggregate = params['aggregate']

        score = sentiment(text_input)

        opinion0 = Sentiment(id= "Opinion_positive",
                             marl__hasPolarity= "marl:Positive",
                             marl__algorithmConfidence= score['pos']
            )
        opinion0.prov(self)
        opinion1 = Sentiment(id= "Opinion_negative",
            marl__hasPolarity= "marl:Negative",
            marl__algorithmConfidence= score['neg']
            )
        opinion1.prov(self)
        opinion2 = Sentiment(id= "Opinion_neutral",
            marl__hasPolarity = "marl:Neutral",
            marl__algorithmConfidence = score['neu']
            )
        opinion2.prov(self)

        if aggregate == 'true':
            res = None
            confident = max(score['neg'],score['neu'],score['pos'])
            if opinion0.marl__algorithmConfidence == confident:
                res = opinion0
            elif opinion1.marl__algorithmConfidence == confident:
                res = opinion1
            elif opinion2.marl__algorithmConfidence == confident:
                res = opinion2
            entry.sentiments.append(res)
        else:
            entry.sentiments.append(opinion0)
            entry.sentiments.append(opinion1)
            entry.sentiments.append(opinion2)

        yield entry

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
