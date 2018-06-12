# -*- coding: utf-8 -*-

import time
import logging
import requests
import json
import string
import os
from os import path
import time
from senpy.plugins import SentimentPlugin
from senpy.models import Results, Entry, Sentiment, Error

import mocked_request

try:
    from unittest import mock
except ImportError:
    import mock

logger = logging.getLogger(__name__)


class MeaningCloudPlugin(SentimentPlugin):
    version = "0.1"

    extra_params = {
        "language": {
            "aliases": ["language", "l"],
            "required": True,
            "options": ["en","es","ca","it","pt","fr","auto"],
            "default": "auto"
        },
        "apikey":{
            "aliases": ["apiKey", "meaningcloud-key", "meaningcloud-apikey"],
            "required": True
        }
    }

    """MeaningCloud plugin uses API from Meaning Cloud to perform sentiment analysis."""
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

        txt = entry['nif:isString']
        api = 'http://api.meaningcloud.com/'
        lang = params.get("language")
        model = "general"
        key = params["apikey"]
        parameters = {
            'key': key,
            'model': model,
            'lang': lang,
            'of': 'json',
            'txt': txt,
            'tt': 'a'
        }
        try:
            r = requests.post(
                api + "sentiment-2.1", params=parameters, timeout=3)
            parameters['lang'] = r.json()['model'].split('_')[1]
            lang = parameters['lang']
            r2 = requests.post(
                api + "topics-2.0", params=parameters, timeout=3)
        except requests.exceptions.Timeout:
            raise Error("Meaning Cloud API does not response")

        api_response = r.json()
        api_response_topics = r2.json()
        if not api_response.get('score_tag'):
            raise Error(r.json())
        entry['language_detected'] = lang
        logger.info(api_response)
        agg_polarity, agg_polarityValue = self._polarity(
            api_response.get('score_tag', None))
        agg_opinion = Sentiment(
            id="Opinion0",
            marl__hasPolarity=agg_polarity,
            marl__polarityValue=agg_polarityValue,
            marl__opinionCount=len(api_response['sentence_list']))
        entry.sentiments.append(agg_opinion)
        logger.info(api_response['sentence_list'])
        count = 1

        for sentence in api_response['sentence_list']:
            for nopinion in sentence['segment_list']:
                logger.info(nopinion)
                polarity, polarityValue = self._polarity(
                    nopinion.get('score_tag', None))
                opinion = Sentiment(
                    id="Opinion{}".format(count),
                    marl__hasPolarity=polarity,
                    marl__polarityValue=polarityValue,
                    marl__aggregatesOpinion=agg_opinion.get('id'),
                    nif__anchorOf=nopinion.get('text', None),
                    nif__beginIndex=nopinion.get('inip', None),
                    nif__endIndex=nopinion.get('endp', None))
                count += 1
                entry.sentiments.append(opinion)

        mapper = {'es': 'es.', 'en': '', 'ca': 'es.', 'it':'it.', 'fr':'fr.', 'pt':'pt.'}

        for sent_entity in api_response_topics['entity_list']:
            
            resource = "_".join(sent_entity.get('form', None).split())
            entity = Sentiment(
                id="Entity{}".format(sent_entity.get('id')),
                marl__describesObject="http://{}dbpedia.org/resource/{}".format(
                    mapper[lang], resource),
                nif__anchorOf=sent_entity.get('form', None),
                nif__beginIndex=sent_entity['variant_list'][0].get('inip', None),
                nif__endIndex=sent_entity['variant_list'][0].get('endp', None))
            entity[
                '@type'] = "ODENTITY_{}".format(
                    sent_entity['sementity'].get('type', None).split(">")[-1])
            entry.entities.append(entity)

        for topic in api_response_topics['concept_list']:
            if 'semtheme_list' in topic:
                for theme in topic['semtheme_list']:
                    concept = Sentiment(
                        id="Topic{}".format(topic.get('id')),
                        prov__wasDerivedFrom="http://dbpedia.org/resource/{}".
                        format(theme['type'].split('>')[-1]))
                    concept[
                        '@type'] = "ODTHEME_{}".format(
                            theme['type'].split(">")[-1])
                    entry.topics.append(concept)
        yield entry

    @mock.patch('requests.post', side_effect=mocked_request.mocked_requests_post)
    def test(self, *args, **kwargs):
        results = list()
        params = {'algo': 'sentiment-meaningCloud', 
                  'intype': 'direct', 
                  'expanded-jsonld': 0, 
                  'informat': 'text', 
                  'prefix': '', 
                  'plugin_type': 'analysisPlugin', 
                  'urischeme': 'RFC5147String', 
                  'outformat': 'json-ld', 
                  'i': 'Hello World', 
                  'input': 'Hello World', 
                  'conversion': 'full', 
                  'language': 'en',
                  'apikey': '00000', 
                  'algorithm': 'sentiment-meaningCloud'}
        for i in range(100):
            res = next(self.analyse_entry(Entry(nif__isString="Hello World Obama"), params))
            results.append(res.sentiments[0]['marl:hasPolarity'])
            results.append(res.topics[0]['prov:wasDerivedFrom'])
            results.append(res.entities[0]['prov:wasDerivedFrom'])

        assert 'marl:Neutral' in results
        assert 'http://dbpedia.org/resource/Astronomy' in results
        assert 'http://dbpedia.org/resource/Obama' in results

if __name__ == '__main__':
    from senpy import easy_test
    easy_test()
