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
