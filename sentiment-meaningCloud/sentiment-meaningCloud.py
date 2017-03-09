import time
import requests
import json
import string
import os
from os import path
import time
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Entry, Sentiment,Error

class DaedalusPlugin(SentimentPlugin):

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
        value = r.json().get('score_tag', None)
        if not value:
            raise Error(r.json())

        #Senpy Response
        response = Results()
        polarityValue = 0
        polarity = 'marl:Neutral'
        if 'N' in value:
            polarity = 'marl:Negative'
            polarityValue = -1
        elif 'P' in value:
            polarity = 'marl:Positive'
            polarityValue = 1

        opinion = Sentiment(id="Opinion0",marl__hasPolarity=polarity,marl__polarityValue = polarityValue)
        entry.sentiments.append(opinion)

        yield entry