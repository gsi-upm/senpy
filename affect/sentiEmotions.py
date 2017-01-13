import time
import requests
import json
import string
import os
import json
import logging
from os import path
import time
from senpy.plugins import SentimentPlugin, SenpyPlugin
from senpy.models import Results, Entry, Sentiment

logger = logging.getLogger(__name__)

class unifiedPlugin(SentimentPlugin):

    def activate(self, *args, **kwargs):
        pass


    def deactivate(self, *args, **kwargs):
        self.close()
     
    
    def analyse(self, **params):

        txt = params["input"]
        endpoint = params["endpoint"]
        lang = params.get("language")
        
        if params["emotions-plugin"] == 'EmoTextWAF':
            lang = 'en'
        sentiplug = params["sentiments-plugin"]
        s_params = {'algo':sentiplug,'language':lang,'i':txt.encode('utf-8')}
        senti_response = Results(requests.get(endpoint, params=s_params).json())
        emoplug = params["emotions-plugin"]
        e_params = {'algo':emoplug,'language':lang,'i':txt.encode('utf-8')}
        emo_response = Results(requests.get(endpoint, params=e_params).json())

        
        #Senpy Response
        response = Results()
        response.analysis = [senti_response.analysis, emo_response.analysis]
        unified = senti_response.entries[0]
        unified["emotions"] = emo_response.entries[0]["emotions"]
        response.entries.append(unified)

        return response