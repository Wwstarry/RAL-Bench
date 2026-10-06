import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'unicall'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'CoalescedFunction', 'kind': 'object', 'signature': ''}, {'name': 'Coalescer', 'kind': 'object', 'signature': ''}, {'name': 'UnhashableArgumentsError', 'kind': 'object', 'signature': ''}, {'name': 'unicall', 'kind': 'object', 'signature': ''}, {'name': 'Backend', 'kind': 'object', 'signature': ''}, {'name': 'DistributedCoalescer', 'kind': 'object', 'signature': ''}, {'name': 'JSONSerializer', 'kind': 'object', 'signature': ''}, {'name': 'RemoteFlightError', 'kind': 'object', 'signature': ''}, {'name': 'Serializer', 'kind': 'object', 'signature': ''}, {'name': 'UnserializableResultError', 'kind': 'object', 'signature': ''}, {'name': 'distributed', 'kind': 'object', 'signature': ''}, {'name': 'Metrics', 'kind': 'object', 'signature': ''}, {'name': 'Stats', 'kind': 'object', 'signature': ''}, {'name': 'stable_hash', 'kind': 'object', 'signature': ''}]
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


def test_documented_unhashable_arguments_raise_clear_error():
    import asyncio
    module = load_module()

    @module.unicall()
    async def consume(value):
        return value

    with pytest.raises(module.UnhashableArgumentsError):
        asyncio.run(consume([1, 2, 3]))

