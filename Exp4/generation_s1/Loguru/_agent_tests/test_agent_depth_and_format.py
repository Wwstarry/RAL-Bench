import re

from loguru import logger


def test_opt_depth_changes_reported_function():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, format="{function}:{message}\n", level="INFO")

    def inner():
        logger.opt(depth=0).info("x")

    def outer():
        inner()

    outer()
    # Should report "inner" (or sometimes wrapper), but with our implementation depth=0 should show caller of .info
    assert out[-1].startswith("inner:x\n")

    out.clear()

    def inner2():
        # depth=1 should shift to outer2
        logger.opt(depth=1).info("y")

    def outer2():
        inner2()

    outer2()
    assert out[-1].startswith("outer2:y\n")


def test_level_alignment_padding():
    out = []

    def sink(m):
        out.append(str(m))

    logger.remove()
    logger.add(sink, format="[{level:<8}] {message}\n", level="DEBUG")
    logger.info("hello")
    assert out[-1] == "[INFO    ] hello\n"