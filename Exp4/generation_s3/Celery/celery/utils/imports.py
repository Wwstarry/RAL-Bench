from __future__ import annotations

import importlib
from typing import Any


def symbol_by_name(name: str) -> Any:
    """
    Import 'pkg.module:attr' or 'pkg.module.attr' and return the attribute.
    """
    if ":" in name:
        module_name, attr = name.split(":", 1)
    else:
        module_name, _, attr = name.rpartition(".")
        if not module_name:
            raise ImportError(f"Not a fully qualified name: {name}")
    module = importlib.import_module(module_name)
    return getattr(module, attr)