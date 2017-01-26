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

    def activate(self, *args, **kwargs):
        pass

    def deactivate(self, *args, **kwargs):
        self.close()
     
    
    def analyse(self, **params):

        txt = params["input"]
        model = params["model"] # general_es / general_es / general_fr
        api = 'http://api.meaningcloud.com/sentiment-2.1'
        lang = params.get("language")
        key = params["apiKey"]
        parameters = {'key': key,'model': model,'lang': lang,'of': 'json','txt': txt,'src': 'its-not-a-real-python-sdk'}
        r = requests.post(api, params=parameters)
        print(r.text)

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
        entry = Entry(id="Entry0",nif_isString=txt)
        opinion = Sentiment(id="Opinion0",marl__hasPolarity=polarity,marl__polarityValue = polarityValue)
        opinion["prov:wasGeneratedBy"] = self.id
        entry.sentiments = []
        entry.sentiments.append(opinion)
        response.entries.append(entry)
        return response
