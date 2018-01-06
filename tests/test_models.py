import logging

import jsonschema

import json
import rdflib
from unittest import TestCase
from senpy.models import (Emotion,
                          EmotionAnalysis,
                          EmotionSet,
                          Entry,
                          Error,
                          Results,
                          Sentiment,
                          SentimentPlugin,
                          Plugins,
                          from_string,
                          from_dict,
                          subtypes)
from senpy import plugins
from pprint import pprint


class ModelsTest(TestCase):
    def test_jsonld(self):
        prueba = {"id": "test", "analysis": [], "entries": []}
        r = Results(**prueba)
        print("Response's context: ")
        pprint(r._context)

        assert r.id == "test"

        j = r.jsonld(with_context=True)
        print("As JSON:")
        pprint(j)
        assert ("@context" in j)
        assert ("marl" in j["@context"])
        assert ("entries" in j["@context"])
        assert (j["@id"] == "test")
        assert "id" not in j

        r6 = Results(**prueba)
        e = Entry({"@id": "ohno", "nif:isString": "Just testing"})
        r6.entries.append(e)
        logging.debug("Reponse 6: %s", r6)
        assert ("marl" in r6._context)
        assert ("entries" in r6._context)
        j6 = r6.jsonld(with_context=True)
        logging.debug("jsonld: %s", j6)
        assert ("@context" in j6)
        assert ("entries" in j6)
        assert ("analysis" in j6)
        resp = r6.flask()
        received = json.loads(resp.data.decode())
        logging.debug("Response: %s", j6)
        assert (received["entries"])
        assert (received["entries"][0]["nif:isString"] == "Just testing")
        assert (received["entries"][0]["nif:isString"] != "Not testing")

    def test_id(self):
        """ Adding the id after creation should overwrite the automatic ID
        """
        r = Entry()
        j = r.jsonld()
        assert '@id' in j
        r.id = "test"
        j2 = r.jsonld()
        assert j2['@id'] == 'test'
        assert 'id' not in j2

    def test_entries(self):
        e = Entry()
        self.assertRaises(jsonschema.ValidationError, e.validate)
        e.nif__isString = "this is a test"
        e.nif__beginIndex = 0
        e.nif__endIndex = 10
        e.validate()

    def test_sentiment(self):
        s = Sentiment()
        self.assertRaises(jsonschema.ValidationError, s.validate)
        s.nif__anchorOf = "so much testing"
        s.prov__wasGeneratedBy = ""
        s.validate()

    def test_emotion_set(self):
        e = EmotionSet()
        self.assertRaises(jsonschema.ValidationError, e.validate)
        e.nif__anchorOf = "so much testing"
        e.prov__wasGeneratedBy = ""
        e.validate()

    def test_results(self):
        r = Results()
        e = Entry()
        e.nif__isString = "Results test"
        r.entries.append(e)
        r.id = ":test_results"
        r.validate()

    def test_plugins(self):
        self.assertRaises(Error, plugins.Plugin)
        p = plugins.SentimentPlugin({"name": "dummy",
                                     "description": "I do nothing",
                                     "version": 0,
                                     "extra_params": {
                                         "none": {
                                             "options": ["es", ],
                                             "required": False,
                                             "default": "0"
                                         }
                                     }})
        c = p.jsonld()
        assert '@type' in c
        assert c['@type'] == 'sentimentPlugin'
        assert 'info' not in c
        assert 'repo' not in c
        assert 'extra_params' in c
        logging.debug('Framed:')
        logging.debug(c)
        p.validate()
        assert 'es' in c['extra_params']['none']['options']
        assert isinstance(c['extra_params']['none']['options'], list)

    def test_str(self):
        """The string representation shouldn't include private variables"""
        r = Results()
        p = plugins.Plugin({"name": "STR test",
                            "description": "Test of private variables.",
                            "version": 0})
        p._testing = 0
        s = str(p)
        assert "_testing" not in s
        r.analysis.append(p)
        s = str(r)
        assert "_testing" not in s

    def test_serialize(self):
        for k, v in subtypes().items():
            e = v()
            e.serialize()

    def test_turtle(self):
        """Any model should be serializable as a turtle file"""
        ana = EmotionAnalysis()
        res = Results()
        res.analysis.append(ana)
        entry = Entry(text='Just testing')
        eSet = EmotionSet()
        emotion = Emotion()
        entry.emotions.append(eSet)
        res.entries.append(entry)
        eSet.onyx__hasEmotion.append(emotion)
        eSet.prov__wasGeneratedBy = ana.id
        triples = ('ana a :Analysis',
                   'entry a :entry',
                   '      nif:isString "Just testing"',
                   '      onyx:hasEmotionSet eSet',
                   'eSet a onyx:EmotionSet',
                   '     prov:wasGeneratedBy ana',
                   '     onyx:hasEmotion emotion',
                   'emotion a onyx:Emotion',
                   'res a :results',
                   '    me:AnalysisInvoloved ana',
                   '    prov:used entry')

        t = res.serialize(format='turtle')
        print(t)
        g = rdflib.Graph().parse(data=t, format='turtle')
        assert len(g) == len(triples)

    def test_plugin_list(self):
        """The plugin list should be of type \"plugins\""""
        plugs = Plugins()
        c = plugs.jsonld()
        assert '@type' in c
        assert c['@type'] == 'plugins'

    def test_single_plugin(self):
        """A response with a single plugin should still return a list"""
        plugs = Plugins()
        p = SentimentPlugin({'id': str(1),
                             'version': 0,
                             'description': 'dummy'})
        plugs.plugins.append(p)
        assert isinstance(plugs.plugins, list)
        js = plugs.jsonld()
        assert isinstance(js['plugins'], list)
        assert js['plugins'][0]['@type'] == 'sentimentPlugin'

    def test_from_string(self):
        results = {
            '@type': 'results',
            '@id': 'prueba',
            'entries': [{
                '@id': 'entry1',
                '@type': 'entry',
                'nif:isString': 'TEST'
            }]
        }
        recovered = from_dict(results)
        assert recovered.id == results['@id']
        assert isinstance(recovered, Results)
        assert isinstance(recovered.entries[0], Entry)

        string = json.dumps(results)
        recovered = from_string(string)
        assert isinstance(recovered, Results)
        assert isinstance(recovered.entries[0], Entry)
