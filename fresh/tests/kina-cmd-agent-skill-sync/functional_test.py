import importlib
import inspect
import os
import sys
import time
from pathlib import Path

import pytest

MODULE = 'skillsync.classifier'
MODULE_ROOT = '.'
SYMBOLS = [{'name': 'classify', 'kind': 'function', 'signature': '(skill, config)'}, {'name': 'classify_all', 'kind': 'function', 'signature': '(skills, config)'}]
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


def test_documented_portable_skill_is_category_a(tmp_path):
    # README.md, "A/B/C/D migration taxonomy".
    from skillsync.config import Config
    from skillsync.model import Skill

    path = tmp_path / "SKILL.md"
    path.write_text("# Portable helper\nUse Python code only.\n", encoding="utf-8")
    skill = Skill("portable", path, "fixture", tmp_path)
    result = load_module().classify(skill, Config())
    assert result.category == "A"
    assert result.missing_deps == []
    assert result.category_reason

