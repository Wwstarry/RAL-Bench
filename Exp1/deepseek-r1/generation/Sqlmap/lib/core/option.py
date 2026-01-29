"""
Copyright (c) 2006-2024 sqlmap developers (https://sqlmap.org/)
See the file 'LICENSE' for copying permission
"""

import sys
from lib.core.data import cmdLineOptions, conf, kb
from lib.core.settings import VERSION

def init():
    """Initialize options (alias for initOptions)"""
    initOptions()

def initOptions():
    """Initialize configuration options"""
    
    # Initialize knowledge base
    kb.originalUrls = []
    kb.targets = []
    kb.injection = {}
    kb.vulnHosts = []
    kb.testMode = False
    kb.matchRatio = None
    kb.heuristicMode = False
    kb.technique = None
    
    # Initialize configuration
    conf.url = cmdLineOptions.get('url')
    conf.data = cmdLineOptions.get('data')
    conf.cookie = cmdLineOptions.get('cookie')
    conf.randomAgent = cmdLineOptions.get('random_agent', False)
    conf.proxy = cmdLineOptions.get('proxy')
    conf.parameter = cmdLineOptions.get('parameter')
    conf.dbms = cmdLineOptions.get('dbms')
    conf.currentUser = cmdLineOptions.get('current_user', False)
    conf.currentDb = cmdLineOptions.get('current_db', False)
    conf.dbs = cmdLineOptions.get('dbs', False)
    conf.tables = cmdLineOptions.get('tables', False)
    conf.columns = cmdLineOptions.get('columns', False)
    conf.dump = cmdLineOptions.get('dump', False)
    conf.batch = cmdLineOptions.get('batch', False)
    conf.flushSession = cmdLineOptions.get('flush_session', False)
    conf.outputDir = cmdLineOptions.get('output_dir')
    
    # Set defaults
    conf.testParameter = None
    conf.verbose = 1
    conf.level = 1
    conf.risk = 1
    conf.threads = 1
    conf.timeSec = 30
    conf.retries = 3
    
    # Check if we have a target
    if not conf.url and not cmdLineOptions.get('google_dork'):
        if not cmdLineOptions.get('help') and not cmdLineOptions.get('hh') and not cmdLineOptions.get('version'):
            print("[!] Missing a mandatory option (-u). Use -h for help and --version for version information")
            sys.exit(1)