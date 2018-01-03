try:
    from unittest.mock import patch, MagicMock
except ImportError:
    from mock import patch, MagicMock


import json
from contextlib import contextmanager

from .models import BaseModel


@contextmanager
def patch_requests(value, code=200):
    success = MagicMock()
    if isinstance(value, BaseModel):
        value = value.jsonld()
    data = json.dumps(value)

    success.json.return_value = value
    success.data.return_value = data
    success.status_code = code

    success.content = json.dumps(value)
    method_mocker = MagicMock()
    method_mocker.return_value = success
    with patch.multiple('requests', request=method_mocker,
                        get=method_mocker, post=method_mocker):
        yield method_mocker, success
        assert method_mocker.called
