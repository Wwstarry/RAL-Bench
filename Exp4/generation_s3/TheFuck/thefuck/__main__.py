from __future__ import annotations

import sys

from .main import main


def _run() -> None:
    raise SystemExit(main(sys.argv[1:]))


if __name__ == "__main__":
    _run()