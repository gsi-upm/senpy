import os
import logging

try:
    import unittest.mock as mock
except ImportError:
    import mock
import json
import os
from unittest import TestCase
from senpy.models import Response
from senpy.plugins import SenpyPlugin

class ModelsTest(TestCase):
    def test_response(self):
        r = Response(context=os.path.normpath(os.path.join(__file__, "..", "..", "context.jsonld")))
        assert("@context" in r)
        assert("marl" in r.context)
        r2 = Response(context=json.loads('{"test": "roger"}'))
        assert("test" in r2.context)
        r3 = Response(context=None)
        del r3.context
        assert("@context" not in r3)
        assert("entries" in r3)
        assert("analysis" in r3)

    def test_opinions(self):
        pass

    def test_frame_plugin(self):
        p = SenpyPlugin({"name": "dummy", "version": 0})
        c = p.frame()
        assert "info" not in c

    def test_frame_response(self):
        pass
