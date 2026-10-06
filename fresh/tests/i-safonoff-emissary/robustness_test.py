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


def test_repeated_import_is_stable():
    first = load_module()
    assert importlib.import_module(MODULE) is first


def test_missing_public_name_raises_attribute_error():
    with pytest.raises(AttributeError):
        getattr(load_module(), "__ral_bench_missing_public_name__")


@pytest.mark.parametrize("spec", SYMBOLS)
def test_public_callables_are_introspectable(spec):
    value = getattr(load_module(), spec["name"])
    if spec["kind"] in {"function", "class"}:
        inspect.signature(value)


def test_retry_after_invalid_input_is_not_guessed():
    # README.md, "Transport and retries": invalid Retry-After returns None.
    module = load_module()
    assert module.parse_retry_after("not-a-delay") is None
    assert module.parse_retry_after("") is None

