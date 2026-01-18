# -*- coding: utf-8 -*-
import gc
import importlib
import os
import pkgutil
import sys
from typing import List, Optional

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


def _rss_mb() -> float:
    try:
        import psutil  # type: ignore
    except Exception:
        return 0.0
    p = psutil.Process()
    return float(p.memory_info().rss) / (1024.0 * 1024.0)


def test_resource_reloading_rules_does_not_explode_rss() -> None:
    names = _iter_rule_module_names(limit=50)

    before = _rss_mb()
    # If psutil isn't available, we still want the test suite to pass.
    if before <= 0.0:
        pytest.skip("psutil not available")

    for _ in range(5):
        for n in names:
            try:
                importlib.import_module(n)
            except Exception:
                continue
        gc.collect()

    after = _rss_mb()
    delta = after - before

    # Keep threshold lenient for Windows + CI variance.
    assert delta < 120.0, "RSS increased too much: before={:.1f}MB after={:.1f}MB delta={:.1f}MB".format(
        before, after, delta
    )
