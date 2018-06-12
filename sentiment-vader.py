# -*- coding: utf-8 -*-

from vaderSentiment import sentiment
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Sentiment, Entry
import logging

logger = logging.getLogger(__name__)

class vaderSentimentPlugin(SentimentPlugin):

    def analyse_entry(self,entry,params):

        logger.debug("Analysing with params {}".format(params))

        text_input = entry.get("text", None)
        aggregate = params['aggregate']

        score = sentiment(text_input)

        opinion0 = Sentiment(id= "Opinion_positive",
                             marl__hasPolarity= "marl:Positive",
                             marl__algorithmConfidence= score['pos']
            )
        opinion1 = Sentiment(id= "Opinion_negative",
            marl__hasPolarity= "marl:Negative",
            marl__algorithmConfidence= score['neg']
            )
        opinion2 = Sentiment(id= "Opinion_neutral",
            marl__hasPolarity = "marl:Neutral",
            marl__algorithmConfidence = score['neu']
            )
        
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
