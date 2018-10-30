import requests
import logging
from . import models

logger = logging.getLogger(__name__)


class Client(object):
    def __init__(self, endpoint):
        self.endpoint = endpoint

    def analyse(self, input, method='GET', **kwargs):
        return self.request('/', method=method, input=input, **kwargs)

    def evaluate(self, input, method='GET', **kwargs):
        return self.request('/evaluate', method=method, input=input, **kwargs)

    def plugins(self, *args, **kwargs):
        resp = self.request(path='/plugins').plugins
        return {p.name: p for p in resp}

    def datasets(self):
        resp = self.request(path='/datasets').datasets
        return {d.name: d for d in resp}

    def request(self, path=None, method='GET', **params):
        url = '{}{}'.format(self.endpoint.rstrip('/'), path)
        if method == 'POST':
            response = requests.post(url=url, data=params)
        else:
            response = requests.request(method=method, url=url, params=params)

        try:
            resp = models.from_dict(response.json())
        except Exception as ex:
            logger.error(('There seems to be a problem with the response:\n'
                          '\tURL: {url}\n'
                          '\tError: {error}\n'
                          '\t\n'
                          '#### Response:\n'
                          '\tCode: {code}'
                          '\tContent: {content}'
                          '\n').format(
                              error=ex,
                              url=url,
                              code=response.status_code,
                              content=response.content))
            raise ex
        if isinstance(resp, models.Error):
            raise resp
        return resp
