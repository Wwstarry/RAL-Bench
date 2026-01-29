#!/usr/bin/env python

"""
Copyright (c) 2023 SQLmap developers (http://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import os
import re
import sys
import time

from lib.core.common import checkConnection
from lib.core.data import conf, cmdLineOptions, kb, logger, paths
from lib.core.settings import IS_WIN, UNICODE_ENCODING

def initOptions():
    """
    Initialize options with default values
    """
    conf.url = None
    conf.direct = None
    conf.data = None
    conf.cookie = None
    conf.level = 1
    conf.risk = 1
    conf.technique = "BEUSTQ"
    conf.threads = 1
    conf.verbose = 1
    conf.timeout = 30
    conf.retries = 3
    conf.delay = 0
    conf.timeSec = 5
    conf.beep = False
    conf.dumpAll = False

def init():
    """
    Initialize configuration and options
    """
    # Call initOptions to set default option values
    initOptions()
    
    # Load command line options to conf
    for key, value in cmdLineOptions.items():
        if value is not None:
            conf[key] = value
    
    # Initialize knowledge base
    kb.testMode = False
    kb.threadContinue = True
    kb.multiThreadMode = False
    kb.injections = []
    kb.dataCaches = {}
    
    # Additional initialization
    if conf.url:
        checkConnection(conf.url)
    
    return True