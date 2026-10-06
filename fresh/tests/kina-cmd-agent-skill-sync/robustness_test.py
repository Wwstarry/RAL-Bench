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


def test_documented_private_convention_requires_rewrite(tmp_path):
    # README.md taxonomy: another agent's tool vocabulary is category C with a reason.
    from skillsync.config import Config
    from skillsync.model import Skill

    path = tmp_path / "SKILL.md"
    path.write_text("Use image_gen to render the result.\n", encoding="utf-8")
    result = load_module().classify(Skill("foreign", path, "fixture", tmp_path), Config())
    assert result.category == "C"
    assert "image_gen" in result.category_reason

