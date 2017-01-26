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
from senpy.models import Results, Entry, Sentiment, Error

logger = logging.getLogger(__name__)

class unifiedPlugin(SentimentPlugin):

    def activate(self, *args, **kwargs):
        pass


    def deactivate(self, *args, **kwargs):
        self.close()
     
    
    def analyse(self, **kwargs):
        params = dict(kwargs)
        txt = params["input"]
        logger.info('TXT:%s' % txt)
        endpoint = params["endpoint"]
        lang = params.get("language")
        key = params["apiKey"]
        sentiplug = params["sentiments-plugin"]
        s_params = params.copy()
        s_params.update({'algo':sentiplug,'language':lang, 'meaningCloud-key':key})
        senti_response = requests.get(endpoint, params=s_params).json()
        logger.info('SENTIPARAMS: %s' % s_params)
        logger.info('SENTIRESPONSE: %s' % senti_response)
        if 'entries' not in senti_response:
            raise Error(senti_response)
        senti_response = Results(senti_response)
        logger.info('SENTI: %s' % senti_response)
        logger.info(senti_response)
        emoplug = params["emotions-plugin"]
        e_params = params.copy()
        e_params.update({'algo':emoplug,'language':lang})
        emo_response = requests.get(endpoint, params=e_params).json()
        if 'entries' not in emo_response:
            raise Error(emo_response)
        emo_response = Results(emo_response)
        logger.info('EMO: %s' % emo_response)
        logger.info(emo_response)



        
        #Senpy Response
        response = Results()
        response.analysis = [senti_response.analysis, emo_response.analysis]
        unified = senti_response.entries[0]
        unified["emotions"] = emo_response.entries[0]["emotions"]
        response.entries.append(unified)

        return response
