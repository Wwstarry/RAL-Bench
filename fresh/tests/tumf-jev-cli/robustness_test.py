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


def test_documented_invalid_json_and_choice_pair_fail_before_network():
    # README.md, "JSON state" and typed choice criteria; invalid input is exit-code 2.
    module = load_module()
    with pytest.raises(module.CliError, match="invalid JSON state"):
        module.state_value("{bad", True)
    with pytest.raises(Exception, match="expected KEY=DESCRIPTION"):
        module.split_pair("missing-separator")

