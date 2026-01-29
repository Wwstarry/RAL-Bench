import re

import termgraph


def _out(capsys):
    return capsys.readouterr().out


def test_formatting_brace_style_and_suffix(capsys):
    d = termgraph.Data(labels=["x"], values=[[1.234]])
    a = termgraph.Args(width=10, format="{:.1f}", suffix="%")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys)
    assert "1.2%" in o


def test_formatting_format_spec_style(capsys):
    d = termgraph.Data(labels=["x"], values=[[1.234]])
    a = termgraph.Args(width=10, format=".2f")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys)
    assert "1.23" in o


def test_barchart_scaling_single_series_width(capsys):
    d = termgraph.Data(labels=["a", "b"], values=[[5], [0]])
    a = termgraph.Args(width=10, format="{:.0f}", suffix="")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys).splitlines()
    assert "#" * 10 in o[0]
    # Second line should not contain a long bar
    assert re.search(r"b:\s*(#*)\s+0", o[1])
    m = re.search(r"b:\s*(#*)\s+0", o[1])
    assert m and len(m.group(1)) == 0


def test_barchart_different_scale_multi_series(capsys):
    # series0 max=10, series1 max=100
    d = termgraph.Data(labels=["a"], values=[[10, 100]])
    a = termgraph.Args(width=8, different_scale=True, format="{:.0f}")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys).splitlines()
    # Two lines (one per series)
    assert len(o) == 2
    # Each should reach full width because each at its own max
    assert "#" * 8 in o[0]
    assert "#" * 8 in o[1]


def test_stackedchart_scaling_and_segment_sum(capsys):
    d = termgraph.Data(labels=["r1", "r2"], values=[[1, 2], [2, 4]])
    a = termgraph.Args(width=12, format="{:.0f}")
    termgraph.StackedChart(d, a).draw()
    lines = _out(capsys).splitlines()
    # totals are 3 and 6; second should have full width, first about half
    assert lines[1].startswith("r2:")
    # extract bar length between "r2: " and trailing space before value
    m2 = re.search(r"^r2:\s*(#+)\s+6", lines[1])
    assert m2, lines[1]
    assert len(m2.group(1)) == 12

    m1 = re.search(r"^r1:\s*(#+)\s+3", lines[0])
    assert m1, lines[0]
    assert 5 <= len(m1.group(1)) <= 7  # ~6 with rounding


def test_no_labels_and_no_values_flags(capsys):
    d = termgraph.Data(labels=["a"], values=[[3]])
    a = termgraph.Args(width=5, no_labels=True, no_values=True)
    termgraph.BarChart(d, a).draw()
    o = _out(capsys).strip()
    assert "a:" not in o
    assert re.fullmatch(r"#+", o) is not None


def test_title_prints_first_line(capsys):
    d = termgraph.Data(labels=["a"], values=[[1]])
    a = termgraph.Args(width=3, title="My Title", format="{:.0f}")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys).splitlines()
    assert o[0] == "My Title"
    assert o[1].startswith("a:")


def test_color_off_by_default_no_ansi(capsys):
    d = termgraph.Data(labels=["a"], values=[[1]])
    a = termgraph.Args(width=3, format="{:.0f}")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys)
    assert "\x1b[" not in o


def test_color_on_emits_ansi(capsys):
    d = termgraph.Data(labels=["a"], values=[[1]])
    a = termgraph.Args(width=3, color=["red"], format="{:.0f}")
    termgraph.BarChart(d, a).draw()
    o = _out(capsys)
    assert "\x1b[" in o