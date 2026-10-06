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


def test_public_module_imports():
    assert load_module().__name__ == MODULE


@pytest.mark.parametrize("spec", SYMBOLS)
def test_declared_public_symbol(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] == "class":
        assert inspect.isclass(value)
    elif spec["kind"] == "function":
        assert callable(value)
    else:
        assert value is not None


@pytest.mark.parametrize("name, expected", list(CONSTANTS.items()))
def test_public_literal_constant(name, expected):
    assert getattr(load_module(), name) == expected


def test_documented_auth_objects_attach_exact_headers():
    # README.md, "Auth": auth objects attach bearer and API-key credentials via httpx.Auth.
    import httpx

    module = load_module()
    bearer = next(module.BearerTokenAuth("secret").auth_flow(httpx.Request("GET", "https://example.test")))
    api_key = next(module.ApiKeyAuth("X-API-Key", "abc").auth_flow(httpx.Request("GET", "https://example.test")))
    assert bearer.headers["Authorization"] == "Bearer secret"
    assert api_key.headers["X-API-Key"] == "abc"

