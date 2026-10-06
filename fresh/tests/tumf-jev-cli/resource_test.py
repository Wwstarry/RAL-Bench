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


def test_public_surface_is_finite():
    module = load_module()
    names = dir(module)
    assert MODULE.split(".")[-1] in module.__name__
    assert len(names) < 10000

