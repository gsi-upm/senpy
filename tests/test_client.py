from unittest import TestCase
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from senpy.client import Client
from senpy.models import Results, Error


class Call(dict):
    def __init__(self, obj):
        self.obj = obj.jsonld()
        self.status_code = 200
        self.content = self.json()

    def json(self):
        return self.obj


class ModelsTest(TestCase):
    def setUp(self):
        self.host = '0.0.0.0'
        self.port = 5000

    def test_client(self):
        endpoint = 'http://dummy/'
        client = Client(endpoint)
        success = Call(Results())
        with patch('requests.request', return_value=success) as patched:
            resp = client.analyse('hello')
            assert isinstance(resp, Results)
        patched.assert_called_with(
            url=endpoint + '/', method='GET', params={'input': 'hello'})
        error = Call(Error('Nothing'))
        with patch('requests.request', return_value=error) as patched:
            try:
                client.analyse(input='hello', algorithm='NONEXISTENT')
                raise Exception('Exceptions should be raised. This is not golang')
            except Error:
                pass
        patched.assert_called_with(
            url=endpoint + '/',
            method='GET',
            params={'input': 'hello',
                    'algorithm': 'NONEXISTENT'})
