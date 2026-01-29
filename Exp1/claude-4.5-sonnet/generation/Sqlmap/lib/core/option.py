"""
Options initialization
"""

from lib.core.data import conf, kb, cmdLineOptions, logger
from lib.core.common import banner, dataToStdout


def initOptions(inputOptions):
    """
    Initialize options from command line
    """
    # Store all options in conf
    for key, value in inputOptions.items():
        conf[key] = value


def init():
    """
    Initialize the environment
    """
    # Initialize knowledge base
    kb.testMode = False
    
    # Show banner if not in quiet mode
    if not conf.get('quiet', False):
        if conf.get('version', False):
            # Just show version, don't show banner
            pass
        elif not conf.get('help', False) and not conf.get('advancedHelp', False):
            dataToStdout(banner())