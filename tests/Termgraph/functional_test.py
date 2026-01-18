from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "termgraph"


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("TERMGRAPH_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "termgraph").resolve()
    return (ROOT / "generation" / "Termgraph").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

# Official Python API: Data, Args, BarChart, StackedChart
from termgraph import (  # type: ignore  # noqa: E402
    Data,
    Args,
    BarChart,
    StackedChart,
)


def _make_args(**overrides: Any) -> Args:
    """Create an Args instance with sensible defaults for tests."""
    base: Dict[str, Any] = {
        "title": None,
        "width": 20,
        "format": "{:>5.1f}",
        "suffix": "",
        "no_labels": False,
        "no_values": False,
        "colors": None,
    }
    base.update(overrides)

    kwargs = {k: v for k, v in base.items() if v is not None}
    return Args(**kwargs)  # type: ignore[arg-type]


def _render_bar(labels: List[str], values: List[List[float]], **arg_overrides: Any) -> str:
    data = Data(values, labels)
    args = _make_args(**arg_overrides)
    chart = BarChart(data, args)
    chart.draw()
    return ""  # draw() prints; caller uses capsys


def _render_stacked(labels: List[str], values: List[List[float]], **arg_overrides: Any) -> str:
    data = Data(values, labels)
    args = _make_args(**arg_overrides)
    chart = StackedChart(data, args)
    chart.draw()
    return ""


def test_simple_horizontal_bar_chart(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["A", "B", "C"]
    values = [[3], [5], [2]]

    data = Data(values, labels)
    args = _make_args(title="Test Chart", width=20, format="{:>5.1f}")

    chart = BarChart(data, args)
    chart.draw()

    captured = capsys.readouterr().out
    assert "Test Chart" in captured
    for label in labels:
        assert label in captured
    assert any(token in captured for token in ("3.0", "5.0", "2.0"))


def test_stacked_chart_multiple_series(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["X", "Y"]
    values = [[1, 2], [3, 4]]

    data = Data(values, labels)
    args = _make_args(title="Stacked Chart", width=30, format="{:>4.1f}")

    chart = StackedChart(data, args)
    chart.draw()

    captured = capsys.readouterr().out
    assert "Stacked Chart" in captured
    for label in labels:
        assert label in captured


def test_bar_chart_object_interface(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["D", "E"]
    values = [[4], [1]]

    data = Data(values, labels)
    args = _make_args(title="Bars", width=10, format="{:>4.1f}")

    chart = BarChart(data, args)
    chart.draw()

    captured = capsys.readouterr().out
    assert "Bars" in captured
    for label in labels:
        assert label in captured


def test_bar_chart_respects_no_values_flag(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["A", "B"]
    values = [[2], [7]]

    data = Data(values, labels)
    args = _make_args(title="No Values", width=12, no_values=True, format="{:>5.1f}")

    BarChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "No Values" in captured
    assert "A" in captured and "B" in captured
    # Happy-path: when no_values=True, the numeric strings should typically be absent.
    assert "2.0" not in captured and "7.0" not in captured


def test_bar_chart_respects_no_labels_flag(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["L1", "L2", "L3"]
    values = [[1], [2], [3]]

    data = Data(values, labels)
    args = _make_args(title="No Labels", width=10, no_labels=True, format="{:>4.1f}")

    BarChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "No Labels" in captured
    # With no_labels=True, label strings should typically not appear.
    assert all(label not in captured for label in labels)
    # Values still appear unless no_values is also enabled.
    assert any(token in captured for token in ("1.0", "2.0", "3.0"))


def test_bar_chart_suffix_appended_to_values(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["CPU", "RAM"]
    values = [[12.5], [7.0]]

    data = Data(values, labels)
    args = _make_args(title="Suffix", width=18, suffix="%", format="{:>4.1f}")

    BarChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "Suffix" in captured
    assert "CPU" in captured and "RAM" in captured
    # Suffix is a key feature for the rendered values.
    assert "%" in captured


def test_bar_chart_custom_format_changes_numeric_rendering(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["P", "Q"]
    values = [[3.14159], [2.71828]]

    data = Data(values, labels)
    args = _make_args(title="Fmt", width=20, format="{:>6.2f}")

    BarChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "Fmt" in captured
    # Expect two-decimal formatting to appear.
    assert "3.14" in captured
    assert "2.72" in captured


def test_stacked_chart_renders_all_labels(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["S1", "S2", "S3"]
    values = [[1, 1], [2, 1], [1, 3]]

    data = Data(values, labels)
    args = _make_args(title="Stack Labels", width=25, format="{:>4.1f}")

    StackedChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "Stack Labels" in captured
    for label in labels:
        assert label in captured


def test_stacked_chart_no_values_still_renders_structure(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["A", "B"]
    values = [[1, 2, 3], [3, 2, 1]]

    data = Data(values, labels)
    args = _make_args(title="Stack No Values", width=30, no_values=True, format="{:>4.1f}")

    StackedChart(data, args).draw()
    captured = capsys.readouterr().out

    assert "Stack No Values" in captured
    assert "A" in captured and "B" in captured
    # With no_values=True, numeric tokens should usually be absent.
    assert "1.0" not in captured and "2.0" not in captured and "3.0" not in captured


def test_title_none_does_not_break_rendering(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["U", "V"]
    values = [[4], [6]]

    data = Data(values, labels)
    args = _make_args(title=None, width=15, format="{:>4.1f}")

    BarChart(data, args).draw()
    captured = capsys.readouterr().out

    # Even without a title, output should include labels and at least one value.
    assert "U" in captured and "V" in captured
    assert any(token in captured for token in ("4.0", "6.0"))


def test_width_parameter_affects_output_presence(capsys: pytest.CaptureFixture[str]) -> None:
    labels = ["W"]
    values = [[9]]

    data = Data(values, labels)

    args_narrow = _make_args(title="Narrow", width=5, format="{:>4.1f}")
    BarChart(data, args_narrow).draw()
    out_narrow = capsys.readouterr().out

    args_wide = _make_args(title="Wide", width=40, format="{:>4.1f}")
    BarChart(data, args_wide).draw()
    out_wide = capsys.readouterr().out

    assert "Narrow" in out_narrow
    assert "Wide" in out_wide
    assert "W" in out_narrow and "W" in out_wide
    # Both should render the numeric value; we don't assert exact bar length (version-dependent).
    assert "9.0" in out_narrow or "9.0" in out_wide
