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


def test_documented_concurrent_calls_coalesce_then_evict():
    import asyncio
    module = load_module()
    calls = 0

    @module.unicall()
    async def lookup(key):
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.01)
        return f"value for {key}"

    async def scenario():
        first = await asyncio.gather(*(lookup("a") for _ in range(20)))
        assert first == ["value for a"] * 20
        assert calls == 1
        assert await lookup("a") == "value for a"
        assert calls == 2

    asyncio.run(scenario())

