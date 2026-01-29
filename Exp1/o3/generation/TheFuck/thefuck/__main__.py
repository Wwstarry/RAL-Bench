"""
Makes ``python -m thefuck`` work exactly like the original entry-point.
"""
import sys
from .main import main

if __name__ == "__main__":          # pragma: no cover
    # ``main`` returns an exit-status – honour it.
    sys.exit(main())