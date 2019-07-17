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
