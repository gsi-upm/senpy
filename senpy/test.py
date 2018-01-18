try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock

from past.builtins import basestring


import json
from contextlib import contextmanager

from .models import BaseModel


@contextmanager
def patch_requests(value, code=200):
    success = MagicMock()
    if isinstance(value, BaseModel):
        value = value.jsonld()
    if not isinstance(value, basestring):
        data = json.dumps(value)
    else:
        data = value

    success.json.return_value = value

    success.status_code = code
    success.content = data
    success.text = data

    method_mocker = MagicMock()
    method_mocker.return_value = success
    with patch.multiple('requests', request=method_mocker,
                        get=method_mocker, post=method_mocker):
        yield method_mocker, success
        assert method_mocker.called
