import os
import logging

try:
    import unittest.mock as mock
except ImportError:
    import mock
import json
import os
from unittest import TestCase
from senpy.models import Response, Entry
from senpy.plugins import SenpyPlugin


class ModelsTest(TestCase):

    def test_response(self):
        r = Response(context=os.path.normpath(
            os.path.join(__file__, "..", "..", "context.jsonld")))
        assert("@context" in r)
        assert(r._frame)
        logging.debug("Default frame: %s", r._frame)
        assert("marl" in r.context)
        assert("entries" in r.context)

        r2 = Response(context=json.loads('{"test": "roger"}'))
        assert("test" in r2.context)

        r3 = Response(context=None)
        del r3.context
        assert("@context" not in r3)
        assert("entries" in r3)
        assert("analysis" in r3)

        r4 = Response()
        assert("@context" in r4)
        assert("entries" in r4)
        assert("analysis" in r4)

        dummy = SenpyPlugin({"name": "dummy", "version": 0})
        r5 = Response({"dummy": dummy}, context=None, frame=None)
        logging.debug("Response 5: %s", r5)
        assert("dummy" in r5)
        assert(r5["dummy"].name == "dummy")
        js = r5.jsonld(context={}, frame={})
        logging.debug("jsonld 5: %s", js)
        assert("dummy" in js)
        assert(js["dummy"].name == "dummy")

        r6 = Response()
        r6.entries.append(Entry(text="Just testing"))
        logging.debug("Reponse 6: %s", r6)
        assert("@context" in r6)
        assert("marl" in r6.context)
        assert("entries" in r6.context)
        js = r6.jsonld()
        logging.debug("jsonld: %s", js)
        assert("entries" in js)
        assert("entries" in js)
        assert("analysis" in js)
        resp = r6.flask()
        received = json.loads(resp.data)
        logging.debug("Response: %s", js)
        assert(received["entries"])
        assert(received["entries"][0]["text"] == "Just testing")
        assert(received["entries"][0]["text"] != "Not testing")

    def test_opinions(self):
        pass

    def test_plugins(self):
        p = SenpyPlugin({"name": "dummy", "version": 0})
        c = p.jsonld()
        assert "info" not in c
        assert "repo" not in c
        assert "params" not in c
        logging.debug("Framed: %s", c)
        assert "extra_params" in c

    def test_frame_response(self):
        pass
