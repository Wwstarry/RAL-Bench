"""
Minimal stubs for 'markdown.extensions' to avoid import errors in clients/tests.

This implementation does not provide full extension support; it only provides
a lightweight surface compatible with basic usage patterns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Union
import importlib


class Extension:
    """Base class stub compatible with Python-Markdown's Extension API."""
    def __init__(self, **kwargs: Any):
        self.config = kwargs

    def extendMarkdown(self, md: Any) -> None:
        return


def load_extensions(
    extensions: Optional[Sequence[Union[str, Extension]]] = None,
    configs: Optional[Dict[str, Dict[str, Any]]] = None,
) -> List[Extension]:
    """Best-effort loader for extensions.

    - If given Extension instances, return them.
    - If given strings, attempt to import and instantiate if possible.
      Unknown extensions are ignored (no-op) to stay permissive.
    """
    if not extensions:
        return []

    configs = configs or {}
    loaded: List[Extension] = []

    for ext in extensions:
        if isinstance(ext, Extension):
            loaded.append(ext)
            continue
        if not isinstance(ext, str):
            continue

        mod_name = ext
        cls_name = None
        # allow "package:ClassName" style
        if ":" in ext:
            mod_name, cls_name = ext.split(":", 1)

        try:
            mod = importlib.import_module(mod_name)
            if cls_name:
                cls = getattr(mod, cls_name, None)
                if cls is not None:
                    loaded.append(cls(**configs.get(ext, {})))
            else:
                # Common convention: module exposes 'makeExtension'
                make = getattr(mod, "makeExtension", None)
                if callable(make):
                    loaded.append(make(**configs.get(ext, {})))
        except Exception:
            # Permissive: ignore unknown/unimportable extensions
            continue

    return loaded