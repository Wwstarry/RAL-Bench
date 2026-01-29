#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# Add the repo root to the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lib.controller.controller import start

if __name__ == "__main__":
    try:
        start()
    except KeyboardInterrupt:
        sys.exit(1)
    except SystemExit as e:
        sys.exit(e.code if e.code is not None else 0)