"""Allow running thefuck as a module with python -m thefuck."""

import sys
from thefuck.main import main

if __name__ == "__main__":
    sys.exit(main())