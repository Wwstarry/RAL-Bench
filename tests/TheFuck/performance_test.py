# -*- coding: utf-8 -*-
import importlib
import os
import pkgutil
import sys
import time
from typing import List, Optional, Tuple

import pytest


def _repo_root() -> str:
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def _ensure_repo_on_syspath() -> None:
    root = _repo_root()
    if root not in sys.path:
        sys.path.insert(0, root)


def _iter_rule_module_names(limit: Optional[int] = None) -> List[str]:
    _ensure_repo_on_syspath()
    importlib.import_module("thefuck")
    rules_pkg = importlib.import_module("thefuck.rules")

    names: List[str] = []
    for m in pkgutil.walk_packages(rules_pkg.__path__, rules_pkg.__name__ + "."):
        if m.ispkg:
            continue
        names.append(m.name)
        if limit is not None and len(names) >= limit:
            break
    return names


def test_performance_import_and_discover_rules_is_fast_enough() -> None:
    t0 = time.time()
    _ensure_repo_on_syspath()
    importlib.import_module("thefuck")
    names = _iter_rule_module_names(limit=200)
    dt = time.time() - t0

    assert len(names) >= 10
    assert dt < 5.0, "import + discover too slow: {:.3f}s".format(dt)


def test_performance_import_first_30_rules_is_fast_enough() -> None:
    names = _iter_rule_module_names(limit=30)
    t0 = time.time()
    ok = 0
    for n in names:
        try:
            importlib.import_module(n)
            ok += 1
        except Exception:
            continue
    dt = time.time() - t0

    assert ok >= 10
    assert dt < 8.0, "importing rules too slow: {:.3f}s (ok={})".format(dt, ok)
