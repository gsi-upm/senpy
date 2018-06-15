from unittest import TestCase

import requests
import json
from senpy.testing import patch_requests
from senpy.models import Results


class TestTest(TestCase):
    def test_patch_text(self):
        with patch_requests('hello'):
            r = requests.get('http://example.com')
            assert r.text == 'hello'
            assert r.content == 'hello'

    def test_patch_json(self):
        r = Results()
        with patch_requests(r):
            res = requests.get('http://example.com')
            assert res.content == json.dumps(r.jsonld())
            js = res.json()
            assert js
            assert js['@type'] == r['@type']

    def test_patch_dict(self):
        r = {'nothing': 'new'}
        with patch_requests(r):
            res = requests.get('http://example.com')
            assert res.content == json.dumps(r)
            js = res.json()
            assert js
            assert js['nothing'] == 'new'
