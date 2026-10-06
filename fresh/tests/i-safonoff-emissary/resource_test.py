import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'emissary'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'ApiKeyAuth', 'kind': 'object', 'signature': ''}, {'name': 'BearerTokenAuth', 'kind': 'object', 'signature': ''}, {'name': 'OAuth2ClientCredentialsAuth', 'kind': 'object', 'signature': ''}, {'name': 'ApiClient', 'kind': 'object', 'signature': ''}, {'name': 'EndpointDefinitionError', 'kind': 'object', 'signature': ''}, {'name': 'PaginationLoopError', 'kind': 'object', 'signature': ''}, {'name': 'endpoint', 'kind': 'object', 'signature': ''}, {'name': 'ErrorMapper', 'kind': 'object', 'signature': ''}, {'name': 'JsonFieldErrorMapper', 'kind': 'object', 'signature': ''}, {'name': 'ApiError', 'kind': 'object', 'signature': ''}, {'name': 'AuthError', 'kind': 'object', 'signature': ''}, {'name': 'ClientError', 'kind': 'object', 'signature': ''}, {'name': 'NotFoundError', 'kind': 'object', 'signature': ''}, {'name': 'RateLimitError', 'kind': 'object', 'signature': ''}, {'name': 'ServerError', 'kind': 'object', 'signature': ''}, {'name': 'UploadFile', 'kind': 'object', 'signature': ''}]
CONSTANTS = {}


def load_module():
    repo = Path(os.environ["RACB_REPO_ROOT"]).resolve()
    root = repo if MODULE_ROOT == "." else repo / MODULE_ROOT
    sys.path.insert(0, str(root))
    return importlib.import_module(MODULE)


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

