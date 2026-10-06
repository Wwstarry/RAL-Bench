import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'jev_ultrafast'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'Agent', 'kind': 'object', 'signature': ''}, {'name': 'Browser', 'kind': 'object', 'signature': ''}]
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


class _BrowserStub:
    def __init__(self, url):
        self.url = url
        self.closed = False

    def observe(self, screenshot=False):
        return {"actions": [], "fingerprint": "page-1", "screenshot": ""}

    def close(self):
        self.closed = True


def test_documented_agent_initial_state_and_goal_normalization(monkeypatch):
    public = load_module()
    agent_module = importlib.import_module("jev_ultrafast.agent")
    monkeypatch.setattr(agent_module, "Browser", _BrowserStub)
    agent = public.Agent("https://example.test", [" Open the page ", "Stop when ready"])
    assert agent.state["goal"] == "Open the page \nStop when ready"
    assert agent.state["plan_index"] == 0
    assert agent.state["status"] == "ready"
    assert agent.state["history"] == []

