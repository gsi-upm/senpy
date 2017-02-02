import logging

import jsonschema

import json
from unittest import TestCase
from senpy.models import Entry, Results, Sentiment, EmotionSet, Error
from senpy.plugins import SenpyPlugin
from pprint import pprint


class ModelsTest(TestCase):
    def test_jsonld(self):
        prueba = {"id": "test", "analysis": [], "entries": []}
        r = Results(**prueba)
        print("Response's context: ")
        pprint(r.context)

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
        r6.entries.append(
            Entry({
                "@id": "ohno",
                "nif:isString": "Just testing"
            }))
        logging.debug("Reponse 6: %s", r6)
        assert ("marl" in r6.context)
        assert ("entries" in r6.context)
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
        ''' Adding the id after creation should overwrite the automatic ID
        '''
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
        self.assertRaises(Error, SenpyPlugin)
        p = SenpyPlugin({"name": "dummy", "version": 0})
        c = p.jsonld()
        assert "info" not in c
        assert "repo" not in c
        assert "extra_params" in c
        logging.debug("Framed:")
        logging.debug(c)
        p.validate()

    def test_str(self):
        """The string representation shouldn't include private variables"""
        r = Results()
        p = SenpyPlugin({"name": "STR test", "version": 0})
        p._testing = 0
        s = str(p)
        assert "_testing" not in s
        r.analysis.append(p)
        s = str(r)
        assert "_testing" not in s

    def test_frame_response(self):
        pass
