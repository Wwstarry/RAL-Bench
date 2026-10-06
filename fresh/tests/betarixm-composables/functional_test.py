import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'composables.agent.protocols'
MODULE_ROOT = 'packages/composables'
SYMBOLS = [{'name': 'Agent', 'kind': 'class', 'signature': 'class'}]
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


def test_documented_agent_interaction_contract_and_independent_state():
    import asyncio
    Agent = load_module().Agent

    class EchoAgent(Agent[str, str]):
        async def interact(self, observation):
            while True:
                observation = yield f"action:{observation}"

    async def scenario():
        agent = EchoAgent()
        first, second = agent.interact("one"), agent.interact("two")
        assert await anext(first) == "action:one"
        assert await anext(second) == "action:two"
        assert await first.asend("next") == "action:next"
        assert await second.asend("other") == "action:other"
        await first.aclose(); await second.aclose()

    asyncio.run(scenario())

