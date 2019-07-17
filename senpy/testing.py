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

from past.builtins import basestring

import os
import responses as requestmock

from .models import BaseModel


MOCK_REQUESTS = os.environ.get('MOCK_REQUESTS', '').lower() in ['no', 'false']


def patch_all_requests(responses):

    patched = requestmock.RequestsMock()

    for response in responses or []:
        args = response.copy()
        if 'json' in args and isinstance(args['json'], BaseModel):
            args['json'] = args['json'].jsonld()
        args['method'] = getattr(requestmock, args.get('method', 'GET'))
        patched.add(**args)
    return patched


def patch_requests(url, response, method='GET', status=200):
    args = {'url': url, 'method': method, 'status': status}
    if isinstance(response, basestring):
        args['body'] = response
    else:
        args['json'] = response
    return patch_all_requests([args])
