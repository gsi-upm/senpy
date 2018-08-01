# -*- coding: utf-8 -*-

import time
import requests
import json
import string
import os
from os import path
import time
from senpy.plugins import SentimentPlugin
from senpy.models import Results, Entry, Entity, Topic, Sentiment, Error


TAIGER_ENDPOINT = os.environ.get("TAIGER_ENDPOINT", 'http://134.244.91.7:8080/sentiment/classifyPositivity')


class TaigerPlugin(SentimentPlugin):
    '''
    Service that analyzes sentiments from social posts written in Spanish or English.

    Example request:

    http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-taiger&inputText=This%20is%20amazing
    '''
    name = 'sentiment-taiger'
    author = 'GSI UPM'
    version = "0.1"
    maxPolarityValue = 0
    minPolarityValue = -10

    def _polarity(self, value):

        if 'neu' in value:
            polarity = 'marl:Neutral'
        elif 'neg' in value:
            polarity = 'marl:Negative'
        elif 'pos' in value:
            polarity = 'marl:Positive'
        return polarity

    def analyse_entry(self, entry, params):

        txt = entry['nif:isString']
        api = TAIGER_ENDPOINT
        parameters = {
            'inputText': txt
        }
        try:
            r = requests.get(
                api, params=parameters, timeout=3)
            api_response = r.json()
        except requests.exceptions.Timeout:
            raise Error("No response from the API")
        except Exception as ex:
            raise Error("There was a problem with the endpoint: {}".format(ex))
        if not api_response.get('positivityCategory'):
            raise Error('No positive category in response: {}'.format(r.json()))
        self.log.debug(api_response)
        agg_polarity = self._polarity(api_response.get('positivityCategory'))
        normalized_text = api_response.get('normalizedText', None)
        agg_opinion = Sentiment(
            id="Opinion0",
            marl__hasPolarity=agg_polarity,
            marl__polarityValue=api_response['positivityScore']
            )
        agg_opinion["normalizedText"] = api_response['normalizedText']
        agg_opinion.prov(self)
        entry.sentiments.append(agg_opinion)

        yield entry

    test_cases = [
        {
            'params': {
                'algo': 'sentiment-taiger',
                'intype': 'direct',
                'expanded-jsonld': 0,
                'informat': 'text',
                'prefix': '',
                'plugin_type': 'analysisPlugin',
                'urischeme': 'RFC5147String',
                'outformat': 'json-ld',
                'conversion': 'full',
                'language': 'en',
                'apikey': '00000',
                'algorithm': 'sentiment-taiger'
            },
            'input': 'I hate to say this',
            'expected': {
                'sentiments': [
                    {'marl:hasPolarity': 'marl:Negative'}],
            },
            'responses': [
                {
                    'url': TAIGER_ENDPOINT,
                    'json': {
                      "inputText": "I hate to say this",
                      "normalizedText": "I hate to say this",
                      "positivityScore": -1.8951251587831475,
                      "positivityCategory": "neg"
                    }
                }
            ]
        },
        {
            'params': {
                'algo': 'sentiment-taiger',
                'intype': 'direct',
                'expanded-jsonld': 0,
                'informat': 'text',
                'prefix': '',
                'plugin_type': 'analysisPlugin',
                'urischeme': 'RFC5147String',
                'outformat': 'json-ld',
                'conversion': 'full',
                'language': 'en',
                'apikey': '00000',
                'algorithm': 'sentiment-taiger'
            },
            'input': 'This is amazing',
            'expected': {
                'sentiments': [
                    {'marl:hasPolarity': 'marl:Positive'}],
            },
            'responses': [
                {
                    'url': TAIGER_ENDPOINT,
                    'json': {
                      "inputText": "This is amazing ",
                      "normalizedText": "This is amazing",
                      "positivityScore": -1.4646806570973374,
                      "positivityCategory": "pos"
                    }
                }
            ]
        },
        {
            'params': {
                'algo': 'sentiment-taiger',
                'intype': 'direct',
                'expanded-jsonld': 0,
                'informat': 'text',
                'prefix': '',
                'plugin_type': 'analysisPlugin',
                'urischeme': 'RFC5147String',
                'outformat': 'json-ld',
                'conversion': 'full',
                'language': 'en',
                'apikey': '00000',
                'algorithm': 'sentiment-taiger'
            },
            'input': 'The pillow is in the wardrobe',
            'expected': {
                'sentiments': [
                    {'marl:hasPolarity': 'marl:Neutral'}],
            },
            'responses': [
                {
                    'url': TAIGER_ENDPOINT,
                    'json': {
                      "inputText": "The pillow is in the wardrobe",
                      "normalizedText": "The pillow is in the wardrobe",
                      "positivityScore": -2.723999097522657,
                      "positivityCategory": "neu"
                    }
                }
            ]
        }


    ]


if __name__ == '__main__':
    from senpy import easy_test
    easy_test()
