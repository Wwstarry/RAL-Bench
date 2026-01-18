"""Helper script to validate tests against the reference Stegano repository.

Usage (from project root):

    python tests/Stegano/run_on_reference.py

This will set STEGANO_TARGET=reference and run all tests under tests/Stegano/.
"""

import os
import sys
from pathlib import Path

import pytest  # type: ignore

ROOT = Path(__file__).resolve().parents[2]

def main() -> int:
    os.environ["STEGANO_TARGET"] = "reference"
    tests_path = ROOT / "tests" / "Stegano"
    return pytest.main([str(tests_path)])

if __name__ == "__main__":
    raise SystemExit(main())
