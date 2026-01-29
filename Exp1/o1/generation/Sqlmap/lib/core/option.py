#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Implements options initialization and any required post-processing logic.
"""

from lib.core.data import conf

def init():
    """
    Initialize default values in the conf dictionary.
    This can be expanded with other default configuration as needed.
    """
    conf['verbose'] = 1
    conf['dryRun'] = False

def initOptions(cmdLineOptions):
    """
    Transfer/interpret parsed cmdLineOptions into the conf dict or other structures.
    """
    for key, value in cmdLineOptions.items():
        conf[key] = value