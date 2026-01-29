"""
Collection of tiny helpers that are shared among several internal modules.
The helpers deliberately keep external dependencies to an absolute minimum.
"""
from __future__ import annotations

import difflib
import os
from pathlib import Path


def iter_executables_on_path() -> set[str]:
    """
    Return a *set* containing the base-names of all executables that are found
    on the current ``$PATH``.

    This result is cached for the lifetime of the interpreter process – the
    environment is not expected to change while the test-suite is running.
    """
    if hasattr(iter_executables_on_path, "_cache"):
        return iter_executables_on_path._cache  # type: ignore[attr-defined]

    result: set[str] = set()
    path_env = os.environ.get("PATH", "")
    for directory in path_env.split(os.pathsep):
        dir_path = Path(directory)
        if not dir_path.is_dir():
            continue
        for entry in dir_path.iterdir():
            if entry.is_file() and os.access(entry, os.X_OK):
                result.add(entry.name)
    iter_executables_on_path._cache = result  # type: ignore[attr-defined]
    return result


def closest_command(name: str) -> list[str]:
    """
    Return a list of commands found on ``$PATH`` that look similar to *name*.

    Similarity is determined via :pyfunc:`difflib.get_close_matches`.
    """
    candidates = iter_executables_on_path()
    # *n* choose up to 5 close matches with a cut-off ratio of 0.6.
    return difflib.get_close_matches(name, candidates, n=5, cutoff=0.6)