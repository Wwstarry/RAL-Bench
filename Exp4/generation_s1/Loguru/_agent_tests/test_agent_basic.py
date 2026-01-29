import os
import re
import io
import tempfile

import pytest

from loguru import logger


def test_add_remove_callable_sink_and_order():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    id1 = logger.add(sink, format="{message}\n", level="DEBUG")
    id2 = logger.add(sink, format="2:{message}\n", level="DEBUG")

    logger.info("A")
    assert out == ["A\n", "2:A\n"]

    logger.remove(id1)
    out.clear()
    logger.info("B")
    assert out == ["2:B\n"]

    logger.remove()
    out.clear()
    logger.info("C")
    assert out == []


def test_file_sink_writes_and_closes():
    logger.remove()
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "x.log")
        hid = logger.add(path, format="{message}\n", level="INFO")
        logger.debug("nope")
        logger.info("yes")
        logger.remove(hid)

        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "yes\n"


def test_default_format_contains_level_and_location():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, level="INFO")  # default format
    logger.info("hello")

    line = out[-1]
    assert " | INFO" in line
    assert " - hello" in line
    assert line.endswith("\n")
    # time prefix looks like 'YYYY-MM-DD HH:mm:ss.SSS'
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3} \|", line)


def test_bind_and_extra_formatting():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, format="{extra[user]}:{message}\n", level="INFO")
    logger.bind(user="alice").info("hi")
    assert out == ["alice:hi\n"]


def test_opt_raw_bypasses_formatting_and_no_newline_added():
    buf = io.StringIO()
    logger.remove()
    logger.add(buf, format="X{message}\n", level="INFO")
    logger.opt(raw=True).info("RAW")
    assert buf.getvalue() == "RAW"


def test_filter_callable_and_disable_enable():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, format="{message}\n", filter=lambda r: "keep" in r["message"], level="DEBUG")
    logger.info("drop")
    logger.info("keep this")
    assert out == ["keep this\n"]

    # disable current module, no output
    out.clear()
    logger.disable(__name__)
    logger.info("keep again")
    assert out == []
    logger.enable(__name__)
    logger.info("keep restored")
    assert out == ["keep restored\n"]


def test_exception_logging_includes_traceback():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, format="{message}{exception}", level="ERROR")

    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("oops")

    text = out[-1]
    assert text.startswith("oops")
    assert "Traceback (most recent call last)" in text
    assert "ZeroDivisionError" in text