#!/usr/local/bin/python
# -*- coding: utf-8 -*-
#
#    Copyright 2014 Grupo de Sistemas Inteligentes (GSI) DIT, UPM
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#


from future.standard_library import install_aliases
install_aliases()

import os

from rdflib import Graph
from senpy.extensions import Senpy
from flask import Flask
from unittest import TestCase

from urllib.parse import urlencode


def parse_resp(resp, fmt):
    return Graph().parse(data=resp.data.decode(), format=fmt)


class SemanticsTest(TestCase):
    '''Tests for the semantics of the server.'''

    @classmethod
    def setUpClass(cls):
        """Set up only once, and re-use in every individual test"""
        cls.app = Flask("test_extensions")
        cls.client = cls.app.test_client()
        cls.senpy = Senpy(plugin_folder=None, default_plugins=True)
        cls.senpy.init_app(cls.app)
        #cls.dir = os.path.join(os.path.dirname(__file__), "..")
        #cls.senpy.add_folder(cls.dir)

    def setUp(self):
        self.app.config['TESTING'] = True  # Tell Flask not to catch Exceptions

    def assertCode(self, resp, code):
        self.assertEqual(resp.status_code, code)

    def test_sentiment(self):
        """
        a sentiment analysis call in json-ld
        """
        # we use expanded json-ld and ignore the context, because in general
        # the context is a uris to the service  and that uri is not
        # available outside of self.client
        params = {
            'input': 'hello',
            'in-headers': True,
            'outformat': 'json-ld',
            'expanded': True,
            'prefix': 'http://default.example/#'
        }
        resp = self.client.get("/api/sentiment-basic?{}".format(urlencode(params)))
        self.assertCode(resp, 200)
        g = parse_resp(resp, fmt='json-ld')
        print('Got this graph: ', g.serialize(format='ttl'))
        assert g
        qres = g.query("""
    prefix prov: <http://www.w3.org/ns/prov#>
    prefix marl: <http://www.gsi.upm.es/ontologies/marl/ns#>
    prefix nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
    prefix onyx: <http://www.gsi.upm.es/ontologies/onyx/ns#>
    prefix senpy: <http://www.gsi.upm.es/ontologies/senpy/ns#>

    SELECT distinct ?entry ?text ?sentiment
    WHERE {
       ?entry a senpy:Entry .
       ?entry marl:hasOpinion ?o .
       ?entry nif:isString ?text .
       ?o marl:hasPolarity ?sentiment .
    }""")
        assert len(qres) == 1, "There should only be one result"
        entry, text, sentiment = list(qres)[0]
        assert str(text) == 'hello', "The returned text does not match the input text."
        assert str(sentiment) in ['marl:Positive', 'marl:Neutral', 'marl:Negative']

    def test_sentiment_turtle(self):
        """
        A sentiment analysis call in turtle format
        """
        params = {
            'input': 'hello',
            'in-headers': True,
            'outformat': 'turtle',
            'expanded': True,
            'prefix': 'http://default.example/#'
        }
        resp = self.client.get("/api/sentiment-basic?{}".format(urlencode(params)))
        self.assertCode(resp, 200)
        g = parse_resp(resp, 'ttl')
        print('Got this graph: ', g.serialize(format='ttl'))
        qres = g.query("""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX marl: <http://www.gsi.upm.es/ontologies/marl/ns#>
    PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
    PREFIX onyx: <http://www.gsi.upm.es/ontologies/onyx/ns#>
    PREFIX senpy: <http://www.gsi.upm.es/ontologies/senpy/ns#>

    SELECT DISTINCT ?entry ?text ?sentiment
       WHERE {
          ?entry a senpy:Entry ;
                 nif:isString ?text ;
                 marl:hasOpinion [
                    marl:hasPolarity ?sentiment
                 ] .
      }""")
        assert len(qres) == 1, "There should only be one row in the result"
        entry, text, sentiment = list(qres)[0]
        assert str(text) == 'hello', "Returned text does not match input text"
        assert str(sentiment) in ['marl:Positive', 'marl:Neutral', 'marl:Negative']

    def test_moral(self):
        """
        An example of a moral analysis, adapted from the examples for the AMOR project:
        http://www.gsi.upm.es/ontologies/amor/examples
        """
        # we use expanded json-ld and ignore the context, because in general
        # the context is a uris to the service  and that uri is not
        # available outside of self.client
        params = {
            'input': 'hello',
            'in-headers': True,
            'outformat': 'json-ld',
            'expanded': True,
            'prefix': 'http://default.example/#'
        }
        resp = self.client.get("/api/sentiment-basic?{}".format(urlencode(params)))
        self.assertCode(resp, 200)
        g = parse_resp(resp, fmt='json-ld')
        print('Got this graph: ', g.serialize(format='ttl'))
        assert g
        qres = g.query("""
        prefix : <http://www.gsi.upm.es/ontologies/amor/examples#>
        prefix amor: <http://www.gsi.upm.es/ontologies/amor/ns#>
        prefix amor-bhv: <http://www.gsi.upm.es/ontologies/amor/models/bhv/ns#>
        prefix amor-mft: <http://www.gsi.upm.es/ontologies/amor/models/mft/ns#>
        prefix bhv: <http://www.gsi.upm.es/ontologies/bhv#>
        prefix mft: <http://www.gsi.upm.es/ontologies/mft/ns#>
        prefix mls: <http://www.w3.org/ns/mls#>
        prefix owl: <http://www.w3.org/2002/07/owl#>
        prefix prov: <http://www.w3.org/ns/prov#>
        prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        prefix schema: <http://schema.org/>

        SELECT ?analysis ?agent ?model ?annotation ?origin ?category
        WHERE {
            ?analysis a amor:MoralValueAnalysis ;
                prov:wasAssociatedWith ?agent ;
                amor:usedMoralValueModel ?model ;
                amor:analysed ?origin ;
                prov:generated ?annotation .
            ?annotation a amor:MoralValueAnnotation ;
                        amor:hasMoralValueCategory ?category .
        }""")
        assert len(qres) == 1
        entry, text, sentiment = list(qres)[0]
        assert entry
        assert str(text) == 'hello'
        assert str(sentiment) in ['marl:positive', 'marl:neutral', 'marl:negative']
