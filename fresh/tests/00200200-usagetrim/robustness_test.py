import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'companion_state'
MODULE_ROOT = 'src/usagetrim/core'
SYMBOLS = [{'name': 'state_dir', 'kind': 'function', 'signature': '()'}, {'name': 'settings', 'kind': 'function', 'signature': '()'}, {'name': 'paused', 'kind': 'function', 'signature': '()'}, {'name': 'update_settings', 'kind': 'function', 'signature': '(**changes)'}, {'name': 'already_wrapped', 'kind': 'function', 'signature': '(command)'}, {'name': 'project_for', 'kind': 'function', 'signature': '(path)'}, {'name': 'client_name', 'kind': 'function', 'signature': '(default)'}]
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


def test_invalid_settings_and_wrapper_detection_are_safe(tmp_path, monkeypatch):
    module = load_module()
    monkeypatch.setenv("USAGETRIM_STATE_DIR", str(tmp_path))
    (tmp_path / "companion.json").write_text("not-json", encoding="utf-8")
    assert module.settings() == {}
    assert module.already_wrapped("ENV=1 usagetrim run pytest") is True
    assert module.already_wrapped("pytest -q") is False
    assert module.already_wrapped("'unterminated") is False

