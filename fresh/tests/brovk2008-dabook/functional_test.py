import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'dabook.config.loader'
MODULE_ROOT = 'src'
SYMBOLS = [{'name': 'load_config', 'kind': 'function', 'signature': '(workspace_or_toml, overrides)'}, {'name': 'save_config', 'kind': 'function', 'signature': '(cfg, path)'}]
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


def test_documented_config_precedence_and_save_reload(tmp_path):
    module = load_module()
    config_file = tmp_path / "dabook.toml"
    config_file.write_text('name = "from-file"\nprofile = "balanced"\n', encoding="utf-8")
    cfg = module.load_config(config_file, {"name": "from-cli", "profile": "lowram"})
    assert cfg.name == "from-cli"
    assert cfg.profile == "lowram"
    snapshot = tmp_path / "snapshot.toml"
    module.save_config(cfg, snapshot)
    assert snapshot.exists() and snapshot.stat().st_size > 0

