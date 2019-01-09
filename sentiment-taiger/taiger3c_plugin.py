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


TAIGER_ENDPOINT = os.environ.get("TAIGER3C_ENDPOINT", 'http://somedi-taiger.hopto.org:5406/es_sentiment_analyzer_3classes')


class TaigerPlugin3cats(SentimentPlugin):
    '''
    Service that analyzes sentiments from social posts written in Spanish or English.

    Example request:

    http://senpy.cluster.gsi.dit.upm.es/api/?algo=sentiment-taiger3c&inputText=This%20is%20amazing
    '''
    name = 'sentiment-taiger3c'
    author = 'GSI UPM'
    version = "0.1"
    maxPolarityValue = -1
    minPolarityValue = 1

    def _polarity(self, value):

        if 'NONE' == value:
            polarity = 'marl:Neutral'
            value = 0
        elif 'N' == value:
            polarity = 'marl:Negative'
            value = -1
        elif 'P' == value:
            polarity = 'marl:Positive'
            value = 1
        else:
            raise ValueError('unknown polarity: {}'.format(value))
        print(value, 'whatsup')
        return polarity, value

    def analyse_entry(self, entry, params):

        txt = entry['nif:isString']
        api = TAIGER_ENDPOINT
        parameters = {
            'text': txt
        }
        try:
            r = requests.get(
                api, params=parameters, timeout=3)
            agg_polarity, value = self._polarity(r.text.strip())
        except requests.exceptions.Timeout:
            raise Error("No response from the API")
        except Exception as ex:
            raise Error("There was a problem with the endpoint: {}".format(ex))
        if not agg_polarity:
            raise Error('No category in response: {}'.format(ar.text))
        self.log.debug(agg_polarity)
        agg_opinion = Sentiment(
            id="Opinion0",
            marl__hasPolarity=agg_polarity,
            marl__polarityValue=value,
            )
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
                    'body': 'N',
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
                    'body': 'P',
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
                    'body': 'NONE',
                }
            ]
        }


    ]


if __name__ == '__main__':
    from senpy import easy_test
    easy_test(debug=False)
