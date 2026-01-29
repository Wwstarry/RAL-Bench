#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import os
import sys
import time
import urllib.parse
import urllib.request

from lib.core.data import paths, logger, kb
from lib.core.settings import VERSION

def banner():
    """
    This function prints sqlmap banner with its version
    """
    _ = """\
    ___ ___[.]_____ ___ ___  {%s}
   |_ -| . [.]     | .'| . |
   |___|_  [.]_|_|_|__,|  _|
         |_|V...       |_|   http://sqlmap.org
    """ % VERSION
    
    print(_)

def setPaths(rootPath):
    """
    Sets absolute paths for project directories and files
    """
    paths.ROOT_PATH = rootPath
    paths.SQLMAP_ROOT_PATH = os.path.join(paths.ROOT_PATH)
    
    paths.SQLMAP_DATA_PATH = os.path.join(paths.SQLMAP_ROOT_PATH, "data")
    paths.SQLMAP_PLUGINS_PATH = os.path.join(paths.SQLMAP_ROOT_PATH, "plugins")
    paths.SQLMAP_OUTPUT_PATH = os.path.join(paths.SQLMAP_ROOT_PATH, "output")
    paths.SQLMAP_DUMP_PATH = os.path.join(paths.SQLMAP_OUTPUT_PATH, "dump")
    paths.SQLMAP_FILES_PATH = os.path.join(paths.SQLMAP_ROOT_PATH, "files")
    
    # Create directories if they don't exist
    for path in (paths.SQLMAP_DATA_PATH, paths.SQLMAP_PLUGINS_PATH, paths.SQLMAP_OUTPUT_PATH, paths.SQLMAP_DUMP_PATH):
        if not os.path.isdir(path):
            try:
                os.makedirs(path, 0o755)
            except:
                pass

def weAreFrozen():
    """
    Returns whether we are frozen via py2exe.
    This will affect how we find out where we are located.
    """
    return hasattr(sys, "frozen")

def checkConnection(url):
    """
    Check if the target URL is accessible
    """
    try:
        urllib.request.urlopen(url, timeout=5)
        return True
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False