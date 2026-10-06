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


def test_repeated_import_lookup_is_bounded():
    start = time.perf_counter()
    module = load_module()
    for _ in range(2000):
        for spec in SYMBOLS[:8]:
            getattr(module, spec["name"])
    assert time.perf_counter() - start < 10.0

