# -*- coding: utf-8 -*-
'''
MeaningCloud plugin uses API from Meaning Cloud to perform sentiment analysis. 

For more information about Meaning Cloud and its services, please visit: https://www.meaningcloud.com/developer/apis

## Usage

To use this plugin, you need to obtain an API key from meaningCloud signing up here: https://www.meaningcloud.com/developer/login

When you had obtained the meaningCloud API Key, you have to provide it to the plugin, using the param **apiKey**.

To use this plugin, you should use a GET Requests with the following possible params:
Params: 
- Language: English (en) and Spanish (es). (default: en)
- API Key: the API key from Meaning Cloud. Aliases: ["apiKey","meaningCloud-key"]. (required)
- Input: text to analyse.(required)
- Model: model provided to Meaning Cloud API (for general domain). (default: general)

## Example of Usage

Example request: 

```
http://senpy.gsi.upm.es/api/?algo=meaningCloud&language=en&apiKey=<put here your API key>&input=I%20love%20Madrid
```
'''

import time
import requests
import json
import string
import os
from os import path
import time
from senpy.plugins import SentimentPlugin
from senpy.models import Results, Entry, Entity, Topic, Sentiment, Error
from senpy.utils import check_template


class MeaningCloudPlugin(SentimentPlugin):
    '''
    Sentiment analysis with meaningCloud service.
    To use this plugin, you need to obtain an API key from meaningCloud signing up here:
    https://www.meaningcloud.com/developer/login

    When you had obtained the meaningCloud API Key, you have to provide it to the plugin, using param apiKey.
    Example request:

    http://senpy.cluster.gsi.dit.upm.es/api/?algo=meaningCloud&language=en&apiKey=YOUR_API_KEY&input=I%20love%20Madrid.
    '''
    name = 'sentiment-meaningcloud'
    author = 'GSI UPM'
    version = "1.1"
    maxPolarityValue = 1
    minPolarityValue = -1

    extra_params = {
        "language": {
            "description": "language of the input",
            "aliases": ["language", "l"],
            "required": True,
            "options": ["en","es","ca","it","pt","fr","auto"],
            "default": "auto"
        },
        "apikey":{
            "description": "API key for the meaningcloud service. See https://www.meaningcloud.com/developer/login",
            "aliases": ["apiKey", "meaningcloud-key", "meaningcloud-apikey"],
            "required": True
        }
    }

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

    def analyse_entry(self, entry, activity):
        params = activity.params

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
        self.log.debug(api_response)
        agg_polarity, agg_polarityValue = self._polarity(
            api_response.get('score_tag', None))
        agg_opinion = Sentiment(
            id="Opinion0",
            marl__hasPolarity=agg_polarity,
            marl__polarityValue=agg_polarityValue,
            marl__opinionCount=len(api_response['sentence_list']))
        agg_opinion.prov(self)
        entry.sentiments.append(agg_opinion)
        self.log.debug(api_response['sentence_list'])
        count = 1

        for sentence in api_response['sentence_list']:
            for nopinion in sentence['segment_list']:
                self.log.debug(nopinion)
                polarity, polarityValue = self._polarity(
                    nopinion.get('score_tag', None))
                opinion = Sentiment(
                    id="Opinion{}".format(count),
                    marl__hasPolarity=polarity,
                    marl__polarityValue=polarityValue,
                    marl__aggregatesOpinion=agg_opinion.get('id'),
                    nif__anchorOf=nopinion.get('text', None),
                    nif__beginIndex=int(nopinion.get('inip', None)),
                    nif__endIndex=int(nopinion.get('endp', None)))
                count += 1
                opinion.prov(self)
                entry.sentiments.append(opinion)

        mapper = {'es': 'es.', 'en': '', 'ca': 'es.', 'it':'it.', 'fr':'fr.', 'pt':'pt.'}

        for sent_entity in api_response_topics['entity_list']:
            resource = "_".join(sent_entity.get('form', None).split())
            entity = Entity(
                id="Entity{}".format(sent_entity.get('id')),
                itsrdf__taIdentRef="http://{}dbpedia.org/resource/{}".format(
                    mapper[lang], resource),
                nif__anchorOf=sent_entity.get('form', None),
                nif__beginIndex=int(sent_entity['variant_list'][0].get('inip', None)),
                nif__endIndex=int(sent_entity['variant_list'][0].get('endp', None)))
            sementity = sent_entity['sementity'].get('type', None).split(">")[-1]
            entity['@type'] = "ODENTITY_{}".format(sementity)
            entity.prov(self)
            if 'senpy:hasEntity' not in entry:
                entry['senpy:hasEntity'] = []
            entry['senpy:hasEntity'].append(entity)

        for topic in api_response_topics['concept_list']:
            if 'semtheme_list' in topic:
                for theme in topic['semtheme_list']:
                    concept = Topic()
                    concept.id = "Topic{}".format(topic.get('id'))
                    concept['@type'] = "ODTHEME_{}".format(theme['type'].split(">")[-1])
                    concept['fam:topic-reference'] = "http://dbpedia.org/resource/{}".format(theme['type'].split('>')[-1])
                    entry.prov(self)
                    if 'senpy:hasTopic' not in entry:
                        entry['senpy:hasTopic'] = []
                    entry['senpy:hasTopic'].append(concept)
        yield entry

    test_cases = [
        {
            'params': {
                'algo': 'sentiment-meaningCloud',
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
                'algorithm': 'sentiment-meaningCloud'
            },
            'input': 'Hello World Obama',
            'expected': {
                'marl:hasOpinion': [
                    {'marl:hasPolarity': 'marl:Neutral'}],
                'senpy:hasEntity': [
                    {'itsrdf:taIdentRef': 'http://dbpedia.org/resource/Obama'}],
                'senpy:hasTopic': [
                    {'fam:topic-reference': 'http://dbpedia.org/resource/Astronomy'}]
            },
            'responses': [
                {
                    'url':  'http://api.meaningcloud.com/sentiment-2.1',
                    'method': 'POST',
                    'json': {
                        'model': 'general_en',
                        'sentence_list': [{
                            'text':
                            'Hello World',
                            'endp':
                            '10',
                            'inip':
                            '0',
                            'segment_list': [{
                                'text':
                                'Hello World',
                                'segment_type':
                                'secondary',
                                'confidence':
                                '100',
                                'inip':
                                '0',
                                'agreement':
                                'AGREEMENT',
                                'endp':
                                '10',
                                'polarity_term_list': [],
                                'score_tag':
                                'NONE'
                            }],
                            'score_tag':
                            'NONE',
                        }],
                        'score_tag':
                        'NONE'
                    }
                }, {
                    'url':  'http://api.meaningcloud.com/topics-2.0',
                    'method': 'POST',
                    'json': {
                        'entity_list': [{
                            'form':
                            'Obama',
                            'id':
                            '__1265958475430276310',
                            'variant_list': [{
                                'endp': '16',
                                'form': 'Obama',
                                'inip': '12'
                            }],
                            'sementity': {
                                'fiction': 'nonfiction',
                                'confidence': 'uncertain',
                                'class': 'instance',
                                'type': 'Top>Person'
                            }
                        }],
                        'concept_list': [{
                            'form':
                            'world',
                            'id':
                            '5c053cd39d',
                            'relevance':
                            '100',
                            'semtheme_list': [{
                                'id': 'ODTHEME_ASTRONOMY',
                                'type': 'Top>NaturalSciences>Astronomy'
                            }]
                        }],
                    }
                }]
        }
    ]


if __name__ == '__main__':
    from senpy import easy_test
    easy_test()
