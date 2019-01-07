#!/usr/local/bin/python
# -*- coding: utf-8 -*-

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
        cls.senpy = Senpy(default_plugins=True)
        cls.senpy.init_app(cls.app)
        cls.dir = os.path.join(os.path.dirname(__file__), "..")
        cls.senpy.add_folder(cls.dir)
        cls.senpy.activate_all()
        cls.senpy.default_plugin = 'Dummy'

    def setUp(self):
        self.app.config['TESTING'] = True  # Tell Flask not to catch Exceptions

    def assertCode(self, resp, code):
        self.assertEqual(resp.status_code, code)

    def test_sentiment(self):
        """
        A sentiment analysis call in JSON-LD
        """
        # We use expanded JSON-LD and ignore the context, because in general
        # the context is a URIS to the service  and that URI is not
        # available outside of self.client
        params = {
            'input': 'hello',
            'in-headers': True,
            'outformat': 'json-ld',
            'expanded': True,
            'prefix': 'http://default.example/#'
        }
        resp = self.client.get("/api/basic?{}".format(urlencode(params)))
        self.assertCode(resp, 200)
        g = parse_resp(resp, fmt='json-ld')
        assert g
        qres = g.query("""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX marl: <http://www.gsi.dit.upm.es/ontologies/marl/ns#>
    PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
    PREFIX onyx: <http://www.gsi.dit.upm.es/ontologies/onyx/ns#>
    PREFIX senpy: <http://www.gsi.upm.es/onto/senpy/ns#>

    SELECT DISTINCT ?entry ?text ?sentiment
       WHERE {
          ?entry a senpy:Entry .
          ?entry marl:hasOpinion ?o .
          ?entry nif:isString ?text .
          ?o marl:hasPolarity ?sentiment .
      }""")
        assert len(qres) == 1
        entry, text, sentiment = list(qres)[0]
        assert entry
        assert str(text) == 'hello'
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
        resp = self.client.get("/api/basic?{}".format(urlencode(params)))
        self.assertCode(resp, 200)
        g = parse_resp(resp, 'ttl')
        qres = g.query("""
    PREFIX prov: <http://www.w3.org/ns/prov#>
    PREFIX marl: <http://www.gsi.dit.upm.es/ontologies/marl/ns#>
    PREFIX nif: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#>
    PREFIX onyx: <http://www.gsi.dit.upm.es/ontologies/onyx/ns#>
    PREFIX senpy: <http://www.gsi.upm.es/onto/senpy/ns#>

    SELECT DISTINCT ?entry ?text ?sentiment
       WHERE {
          ?entry a senpy:Entry .
          ?entry marl:hasOpinion ?o .
          ?entry nif:isString ?text .
          ?o marl:hasPolarity ?sentiment .
      }""")
        assert len(qres) == 1
        entry, text, sentiment = list(qres)[0]
        assert entry
        assert str(text) == 'hello'
        assert str(sentiment) in ['marl:Positive', 'marl:Neutral', 'marl:Negative']
