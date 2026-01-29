"""
Common functions
"""

import os
import sys

from lib.core.data import conf, kb
from lib.core.settings import VERSION, DESCRIPTION, APPLICATION


def setPaths():
    """
    Set up application paths
    """
    root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    conf.root_path = root_path


def banner():
    """
    Display application banner
    """
    _ = """
        ___
       __H__
 ___ ___[.]_____ ___ ___  {%s}
|_ -| . [']     | .'| . |
|___|_  ["]_|_|_|__,|  _|
      |_|V...       |_|   %s

""" % (VERSION, DESCRIPTION)
    
    return _


def dataToStdout(data, forceOutput=False):
    """
    Write data to stdout
    """
    try:
        sys.stdout.write(data)
        sys.stdout.flush()
    except (IOError, UnicodeError):
        pass