from __future__ import annotations

import sys
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    """
    Minimal console entry point placeholder.

    The reference project provides a rich CLI; for this kata we only need this
    module to be importable. This function prints a short help and exits.
    """
    if argv is None:
        argv = sys.argv[1:]
    out = (
        "stegano.console.main: minimal placeholder CLI.\n"
        "This repository implements the library APIs (lsb/red/exifHeader/wav).\n"
    )
    sys.stdout.write(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())