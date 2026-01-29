#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import collections

# Dictionary-like structures for global variables

# Object to store configuration options
conf = collections.OrderedDict()

# Object to store command line options
cmdLineOptions = collections.OrderedDict()

# Object to store knowledge base data
kb = collections.OrderedDict()

# Object to store various paths
paths = collections.OrderedDict()

# Logger placeholder (will be initialized later)
class Logger:
    def debug(self, msg):
        print(f"[DEBUG] {msg}")
    
    def info(self, msg):
        print(f"[INFO] {msg}")
    
    def warning(self, msg):
        print(f"[WARNING] {msg}")
    
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def critical(self, msg):
        print(f"[CRITICAL] {msg}")

logger = Logger()