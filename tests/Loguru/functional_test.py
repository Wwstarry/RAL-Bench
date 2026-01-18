from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path
from typing import Callable, Tuple

import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement (preferred): use RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/loguru/__init__.py
#   - <repo_root>/src/loguru/__init__.py
#
# Local fallback (no absolute path hardcode): keep original eval layout:
#   <eval_root>/repositories/loguru  OR  <eval_root>/generation/Loguru
# ---------------------------------------------------------------------------

PACKAGE_NAME = "loguru"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.environ.get("LOGURU_TARGET", "generated").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "loguru"
    elif target == "generated":
        REPO_ROOT = ROOT / "generation" / "Loguru"
    else:
        pytest.skip(
            "Unknown LOGURU_TARGET={!r}".format(target),
            allow_module_level=True,
        )

if not REPO_ROOT.exists():
    pytest.skip(
        "Target repository does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

try:
    from loguru import logger  # type: ignore  # noqa: E402
except Exception as exc:
    pytest.skip(
        "Failed to import loguru from {}: {}".format(REPO_ROOT, exc),
        allow_module_level=True,
    )


def make_buffer_logger(
    fmt: str = "{level}:{message}",
    level: str = "DEBUG",
    *,
    colorize: bool = False,
    serialize: bool = False,
    filter_: Callable[..., bool] = None,
) -> Tuple["logger.__class__", io.StringIO]:
    """Create a logger configured with a single StringIO sink (happy-path)."""
    buf = io.StringIO()
    logger.remove()
    add_kwargs = {"format": fmt, "level": level, "colorize": colorize, "serialize": serialize}
    if filter_ is not None:
        add_kwargs["filter"] = filter_
    logger.add(buf, **add_kwargs)
    return logger, buf


def _lines(buf: io.StringIO) -> list:
    return [line.strip() for line in buf.getvalue().splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# Functional tests (happy-path only) - >= 10 independent test_* functions
# ---------------------------------------------------------------------------

def test_basic_levels_and_formatting() -> None:
    log, buf = make_buffer_logger(fmt="{level}:{message}", level="DEBUG")

    log.debug("debug-msg")
    log.info("info-msg")
    log.warning("warn-msg")

    lines = _lines(buf)
    assert len(lines) >= 3
    assert any(line.startswith("DEBUG:") and "debug-msg" in line for line in lines)
    assert any(line.startswith("INFO:") and "info-msg" in line for line in lines)
    assert any(line.startswith("WARNING:") and "warn-msg" in line for line in lines)


def test_level_filtering() -> None:
    log, buf = make_buffer_logger(fmt="{level}:{message}", level="INFO")

    log.debug("should-be-filtered")
    log.info("visible-info")

    output = buf.getvalue()
    assert "should-be-filtered" not in output
    assert "visible-info" in output


def test_log_method_with_level_name() -> None:
    log, buf = make_buffer_logger(fmt="{level}:{message}", level="DEBUG")

    log.log("INFO", "hello-info")
    log.log("WARNING", "hello-warn")

    lines = _lines(buf)
    assert any(line.startswith("INFO:") and "hello-info" in line for line in lines)
    assert any(line.startswith("WARNING:") and "hello-warn" in line for line in lines)


def test_bind_extra_renders_fields() -> None:
    log, buf = make_buffer_logger(fmt="{level}:{message} user={extra[user]} req={extra[request_id]}")

    bound = log.bind(user="alice", request_id="req-123")
    bound.info("hello")

    out = buf.getvalue()
    assert "INFO:" in out
    assert "hello" in out
    assert "user=alice" in out
    assert "req=req-123" in out


def test_contextualize_adds_extra_fields() -> None:
    log, buf = make_buffer_logger(fmt="{message} user={extra[user]}")

    with log.contextualize(user="bob"):
        log.info("ctx-hello")

    out = buf.getvalue()
    assert "ctx-hello" in out
    assert "user=bob" in out


def test_multiple_sinks_receive_same_message() -> None:
    buf1 = io.StringIO()
    buf2 = io.StringIO()

    logger.remove()
    logger.add(buf1, format="{level}:{message}", level="INFO")
    logger.add(buf2, format="{level}:{message}", level="INFO")

    logger.info("fanout")

    out1 = buf1.getvalue()
    out2 = buf2.getvalue()
    assert "fanout" in out1
    assert "fanout" in out2
    assert "INFO" in out1
    assert "INFO" in out2


def test_add_file_sink_writes_lines(tmp_path: Path) -> None:
    log_path = tmp_path / "loguru_test.log"

    logger.remove()
    logger.add(log_path, format="{level}:{message}", level="INFO")

    logger.info("file-line-1")
    logger.warning("file-line-2")

    assert log_path.exists()
    text = log_path.read_text(encoding="utf-8")
    assert "INFO:file-line-1" in text
    assert "WARNING:file-line-2" in text


def test_serialize_output_contains_message_and_level() -> None:
    # serialize=True should emit JSON per record into the sink
    log, buf = make_buffer_logger(level="INFO", serialize=True)

    log.info("json-msg")

    raw_lines = _lines(buf)
    assert len(raw_lines) >= 1

    record = json.loads(raw_lines[-1])
    assert isinstance(record, dict)
    assert "record" in record
    assert isinstance(record["record"], dict)
    assert record["record"]["message"] == "json-msg"
    assert record["record"]["level"]["name"] == "INFO"


def test_patch_can_enrich_record_extra() -> None:
    # patch() lets us enrich record data in a typical usage pattern
    log, buf = make_buffer_logger(fmt="{message} patched={extra[patched]}")

    patched = log.patch(lambda r: r["extra"].update({"patched": "yes"}))
    patched.info("hello")

    out = buf.getvalue()
    assert "hello" in out
    assert "patched=yes" in out


def test_filter_callable_allows_subset_of_records() -> None:
    def only_info(record) -> bool:
        return record["level"].name == "INFO"

    log, buf = make_buffer_logger(fmt="{level}:{message}", level="DEBUG", filter_=only_info)

    log.debug("nope")
    log.info("yep")

    out = buf.getvalue()
    assert "nope" not in out
    assert "yep" in out
    assert "INFO:" in out


def test_time_and_level_in_default_format() -> None:
    # Default format should include some timestamp-like content, level, and message.
    buf = io.StringIO()
    logger.remove()
    logger.add(buf)

    logger.info("default-format-test")

    output = buf.getvalue()
    assert "INFO" in output
    assert "default-format-test" in output
    assert any(ch.isdigit() for ch in output)
    assert ":" in output
