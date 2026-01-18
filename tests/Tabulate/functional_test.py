from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Sequence, Tuple

import pytest

# -----------------------------------------------------------------------------
# RACB import contract:
# - Use RACB_REPO_ROOT as the repository root when provided (runner sets it).
# - Auto-detect two layouts:
#     repo_root/<package>/__init__.py
#     repo_root/src/<package>/__init__.py   -> insert repo_root/src
#
# Note: python-tabulate is sometimes shipped as a single module (tabulate.py)
# rather than a package directory. We still honor the required package checks
# first, then fall back to detecting tabulate.py under repo_root or repo_root/src.
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "tabulate"


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("TABULATE_TARGET", "generated").lower()
    if target == "reference":
        return (ROOT / "repositories" / "python-tabulate").resolve()
    if target == "generated":
        return (ROOT / "generation" / "Tabulate").resolve()
    raise RuntimeError("Unknown TABULATE_TARGET={!r}".format(target))


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

# Required detection rules (package layout)
src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE / "__init__.py"

# Fallback detection (module layout)
src_module = REPO_ROOT / "src" / (PACKAGE + ".py")
root_module = REPO_ROOT / (PACKAGE + ".py")

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
elif src_module.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_module.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not locate import target for 'tabulate'. Expected one of: {}, {}, {}, {}".format(
            src_pkg_init, root_pkg_init, src_module, root_module
        ),
        allow_module_level=True,
    )

from tabulate import tabulate  # type: ignore  # noqa: E402


def _lines(s: str) -> List[str]:
    return [line.rstrip("\n") for line in s.strip().splitlines() if line.strip()]


def test_basic_list_of_lists_default_simple() -> None:
    table = [
        ["Sun", 696000, 1.9891e9],
        ["Earth", 6371, 5973.6],
        ["Moon", 1737, 73.5],
        ["Mars", 3390, 641.85],
    ]

    output = tabulate(table)
    assert isinstance(output, str)
    lines = _lines(output)

    assert any("Sun" in line and "696000" in line for line in lines)
    assert any("Earth" in line and "6371" in line for line in lines)
    assert any("Moon" in line and "1737" in line for line in lines)
    assert any("Mars" in line and "641.85" in line for line in lines)


def test_headers_as_list_and_plain_format() -> None:
    table = [
        ["spam", 42],
        ["eggs", 451],
        ["bacon", 0],
    ]
    headers = ["item", "qty"]

    output = tabulate(table, headers=headers, tablefmt="plain")
    lines = _lines(output)

    assert lines[0].strip().startswith("item")
    assert "qty" in lines[0]
    assert "spam" in lines[1] and "42" in lines[1]
    assert "eggs" in lines[2] and "451" in lines[2]
    assert "bacon" in lines[3] and "0" in lines[3]


def test_headers_firstrow_and_simple_format() -> None:
    table = [
        ["Name", "Age"],
        ["Alice", 24],
        ["Bob", 19],
    ]

    output = tabulate(table, headers="firstrow", tablefmt="simple")
    lines = _lines(output)

    assert lines[0].strip().startswith("Name")
    assert "Age" in lines[0]
    # separator line usually contains dashes
    assert "-" in lines[1].replace(" ", "")
    assert any("Alice" in line and "24" in line for line in lines)
    assert any("Bob" in line and "19" in line for line in lines)


def test_headers_keys_on_dict_of_iterables() -> None:
    table = {
        "Name": ["Alice", "Bob"],
        "Age": [24, 19],
    }

    output = tabulate(table, headers="keys")
    lines = _lines(output)

    assert "Name" in lines[0]
    assert "Age" in lines[0]

    joined = "\n".join(lines)
    assert "Alice" in joined and "24" in joined
    assert "Bob" in joined and "19" in joined


def test_showindex_variants() -> None:
    table = [
        ["F", 24],
        ["M", 19],
    ]

    out_true = tabulate(table, showindex=True)
    lines_true = _lines(out_true)
    assert any(line.lstrip().startswith("0") for line in lines_true)
    assert any(line.lstrip().startswith("1") for line in lines_true)

    out_false = tabulate(table, showindex=False)
    lines_false = _lines(out_false)
    assert not any(line.lstrip().startswith("0 ") for line in lines_false)
    assert not any(line.lstrip().startswith("1 ") for line in lines_false)


def test_github_and_grid_formats() -> None:
    table = [
        ["item", "qty"],
        ["spam", 42],
        ["eggs", 451],
        ["bacon", 0],
    ]

    out_github = tabulate(table[1:], headers=table[0], tablefmt="github")
    lines_gh = _lines(out_github)
    assert lines_gh[0].startswith("|")
    assert lines_gh[0].endswith("|")
    assert any("spam" in line for line in lines_gh)
    assert any("eggs" in line for line in lines_gh)

    out_grid = tabulate(table[1:], headers=table[0], tablefmt="grid")
    lines_grid = _lines(out_grid)
    assert lines_grid[0].startswith("+") and lines_grid[0].endswith("+")
    joined = "\n".join(lines_grid)
    assert "item" in joined and "qty" in joined
    assert "spam" in joined and "eggs" in joined and "bacon" in joined


def test_list_of_dicts_headers_keys_plain() -> None:
    rows = [
        {"name": "Alice", "score": 10},
        {"name": "Bob", "score": 12},
    ]
    output = tabulate(rows, headers="keys", tablefmt="plain")
    lines = _lines(output)

    header = lines[0]
    assert "name" in header
    assert "score" in header

    joined = "\n".join(lines)
    assert "Alice" in joined and "10" in joined
    assert "Bob" in joined and "12" in joined


def test_missingval_renders_placeholder() -> None:
    rows = [
        ["Alice", None],
        ["Bob", "ok"],
    ]
    output = tabulate(rows, headers=["name", "status"], tablefmt="plain", missingval="N/A")
    lines = _lines(output)

    joined = "\n".join(lines)
    assert "Alice" in joined
    assert "Bob" in joined
    assert "N/A" in joined
    assert "ok" in joined


def test_floatfmt_controls_numeric_rendering() -> None:
    rows = [
        ["pi", 3.14159],
        ["e", 2.71828],
    ]
    output = tabulate(rows, headers=["name", "value"], tablefmt="plain", floatfmt=".2f")
    lines = _lines(output)

    joined = "\n".join(lines)
    assert "pi" in joined and "3.14" in joined
    assert "e" in joined and "2.72" in joined


def test_disable_numparse_preserves_numeric_strings() -> None:
    rows = [
        ["code", "value"],
        ["A", "001"],
        ["B", "010"],
    ]
    output = tabulate(rows[1:], headers=rows[0], tablefmt="plain", disable_numparse=True)
    lines = _lines(output)

    joined = "\n".join(lines)
    assert "001" in joined
    assert "010" in joined


def test_maxcolwidths_wraps_long_text() -> None:
    long_text = "alpha beta gamma delta epsilon zeta"
    rows = [
        ["id", "note"],
        [1, long_text],
        [2, "short"],
    ]
    output = tabulate(
        rows[1:],
        headers=rows[0],
        tablefmt="simple",
        maxcolwidths=[None, 10],
    )
    lines = _lines(output)

    # With wrapping, the output typically spans more than (header + separator + 2 rows).
    assert len(lines) >= 5
    joined = "\n".join(lines)
    # Ensure both a long token and a later token appear somewhere in the rendered table.
    assert "alpha" in joined
    assert "epsilon" in joined
    assert "short" in joined


def test_pipe_format_has_pipes_and_headers() -> None:
    rows = [
        ["name", "qty"],
        ["spam", 42],
        ["eggs", 451],
    ]
    output = tabulate(rows[1:], headers=rows[0], tablefmt="pipe")
    lines = _lines(output)

    # Pipe tables use | delimiters; keep assertions permissive.
    assert "|" in lines[0]
    joined = "\n".join(lines)
    assert "name" in joined and "qty" in joined
    assert "spam" in joined and "42" in joined
    assert "eggs" in joined and "451" in joined
