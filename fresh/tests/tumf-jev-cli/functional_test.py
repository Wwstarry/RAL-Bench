import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'jev_cli'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'annotations', 'kind': 'object', 'signature': ''}, {'name': 'Path', 'kind': 'object', 'signature': ''}, {'name': 'Any', 'kind': 'object', 'signature': ''}, {'name': 'CliError', 'kind': 'class', 'signature': 'class'}, {'name': 'masked_getpass', 'kind': 'function', 'signature': '(prompt)'}, {'name': 'api_key', 'kind': 'function', 'signature': '(provider)'}, {'name': 'set_api_key', 'kind': 'function', 'signature': '(provider)'}, {'name': 'install_skills', 'kind': 'function', 'signature': '(global_install, claude, cwd, home)'}, {'name': 'read_text', 'kind': 'function', 'signature': '(value)'}, {'name': 'state_value', 'kind': 'function', 'signature': '(value, force_json)'}, {'name': 'split_pair', 'kind': 'function', 'signature': '(value)'}, {'name': 'load_request', 'kind': 'function', 'signature': '(path)'}, {'name': 'provider_request', 'kind': 'function', 'signature': '(payload, provider)'}, {'name': 'normalize_response', 'kind': 'function', 'signature': '(result, provider)'}, {'name': 'provider_endpoint', 'kind': 'function', 'signature': '(provider, override)'}, {'name': 'provider_model', 'kind': 'function', 'signature': '(provider)'}]
CONSTANTS = {'INSTALL_MARKER': '.jev-cli-managed'}


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


def test_documented_json_state_pairs_and_provider_defaults():
    # README.md, "JSON state", "Authentication", and provider table.
    module = load_module()
    assert module.state_value('{"message":"today"}', True) == {"message": "today"}
    assert module.split_pair("billing=Payment issue") == ("billing", "Payment issue")
    assert module.provider_model("official") == "jev-latest"
    assert module.provider_model("vercel") == "typesafe-ai/jev"
    assert module.provider_model("openrouter") == "typesafe/jev-1.13"
    assert module.provider_endpoint("custom", "https://proxy.example/api") == "https://proxy.example/api"

