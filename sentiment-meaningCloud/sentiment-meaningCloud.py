import time
import logging
import requests
import json
import string
import os
from os import path
import time
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Entry, Sentiment,Error

logger = logging.getLogger(__name__)

class DaedalusPlugin(SentimentPlugin):
    

    def _polarity(self, value):

        if 'NONE' in value:
            polarity = 'marl:Neutral'
            polarityValue = 0
        elif 'N' in value:        
            polarity = 'marl:Negative'
            polarityValue = -1
        elif 'P' in value:
            polarity = 'marl:Positive'
            polarityValue = 1
        return polarity, polarityValue

    def analyse_entry(self, entry, params):

        txt = entry.get("text",None)
        model = "general" # general_es / general_es / general_fr
        api = 'http://api.meaningcloud.com/sentiment-2.1'
        lang = params.get("language")
        key = params["apiKey"]
        parameters = {'key': key,
                      'model': model,
                      'lang': lang,
                      'of': 'json',
                      'txt': txt,
                      'src': 'its-not-a-real-python-sdk'
                      }
        try:
            r = requests.post(api, params=parameters, timeout=3)
        except requests.exceptions.Timeout:
            raise Error("Meaning Cloud API does not response")
        api_response = r.json()
        if not api_response.get('score_tag'):
            raise Error(r.json())
        logger.info(api_response)
        response = Results()
        agg_polarity, agg_polarityValue = self._polarity(api_response.get('score_tag', None))
        agg_opinion = Sentiment(id="Opinion0",
                                marl__hasPolarity=agg_polarity,
                                marl__polarityValue = agg_polarityValue, 
                                marl__opinionCount = len(api_response['sentence_list']))
        entry.sentiments.append(agg_opinion)
        logger.info(api_response['sentence_list'])
        count = 1
        for sentence in api_response['sentence_list']:
            for nopinion in sentence['segment_list']:        
                logger.info(nopinion)
                polarity, polarityValue = self._polarity(nopinion.get('score_tag', None))
                opinion = Sentiment(id="Opinion{}".format(count), 
                                    marl__hasPolarity=polarity, 
                                    marl__polarityValue=polarityValue,
                                    marl__aggregatesOpinion=agg_opinion.get('id'),
                                    nif__anchorOf=nopinion.get('text', None),
                                    nif__beginIndex=nopinion.get('inip', None),
                                    nif__endIndex=nopinion.get('endp', None)
                                    )

                count += 1
                entry.sentiments.append(opinion)
        yield entry
