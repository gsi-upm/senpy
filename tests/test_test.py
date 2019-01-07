from unittest import TestCase

import requests
import json
from senpy.testing import patch_requests
from senpy.models import Results

ENDPOINT = 'http://invalid.com'


class TestTest(TestCase):
    def test_patch_text(self):
        with patch_requests(ENDPOINT, 'hello'):
            r = requests.get(ENDPOINT)
            assert r.text == 'hello'

    def test_patch_json(self):
        r = Results()
        with patch_requests(ENDPOINT, r):
            res = requests.get(ENDPOINT)
            assert res.text == json.dumps(r.jsonld())
            js = res.json()
            assert js
            assert js['@type'] == r['@type']

    def test_patch_dict(self):
        r = {'nothing': 'new'}
        with patch_requests(ENDPOINT, r):
            res = requests.get(ENDPOINT)
            assert res.text == json.dumps(r)
            js = res.json()
            assert js
            assert js['nothing'] == 'new'
