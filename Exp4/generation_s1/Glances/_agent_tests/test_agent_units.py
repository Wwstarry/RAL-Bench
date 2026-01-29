import pytest

from glances.csvout import parse_fields, validate_fields
from glances.errors import UnknownFieldError, UsageError
from glances.metrics import get_snapshot


def test_parse_fields_strips():
    assert parse_fields(" now , cpu.user ") == ["now", "cpu.user"]


def test_parse_fields_rejects_empty():
    with pytest.raises(UsageError):
        parse_fields("")
    with pytest.raises(UsageError):
        parse_fields("now,,cpu.user")


def test_validate_fields_unknown():
    with pytest.raises(UnknownFieldError) as ei:
        validate_fields(["now", "nope"])
    assert "nope" in str(ei.value)


def test_snapshot_has_required_keys_and_numeric():
    snap = get_snapshot()
    for k in ["now", "cpu.user", "cpu.total", "mem.used", "load"]:
        assert k in snap
    # Must be parseable as floats when stringified
    float(str(snap["now"]))
    float(str(snap["cpu.user"]))
    float(str(snap["cpu.total"]))
    float(str(snap["mem.used"]))
    float(str(snap["load"]))