import re
import termgraph


def test_public_api_importable():
    assert hasattr(termgraph, "Data")
    assert hasattr(termgraph, "Args")
    assert hasattr(termgraph, "BarChart")
    assert hasattr(termgraph, "StackedChart")


def test_data_normalization_row_major():
    d = termgraph.Data(labels=["a", "b", "c"], values=[[1, 2], [3, 4], [5, 6]])
    assert d.n_rows == 3
    assert d.n_series == 2
    assert d.values == [[1, 2], [3, 4], [5, 6]]


def test_data_normalization_series_major_transpose():
    d = termgraph.Data(labels=["a", "b", "c"], values=[[1, 3, 5], [2, 4, 6]])
    assert d.values == [[1, 2], [3, 4], [5, 6]]
    assert d.n_series == 2


def test_data_invalid_shape_raises():
    try:
        termgraph.Data(labels=["a", "b"], values=[[1, 2, 3]])
    except ValueError as e:
        assert "shape" in str(e) or "rectangular" in str(e)
    else:
        raise AssertionError("Expected ValueError")