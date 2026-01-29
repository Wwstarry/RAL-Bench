"""
Core data structures for shared runtime state
"""

class _CmdLineOptions:
    """Command line options container"""
    def __init__(self):
        self.url = None
        self.data = None
        self.cookie = None
        self.randomAgent = False
        self.level = 1
        self.risk = 1
        self.verbose = 1
        self.batch = False
        self.update = False
        self.version = False
        self.help = False
        self.advancedHelp = False

class _Conf:
    """Configuration container"""
    def __init__(self):
        self.url = None
        self.data = None
        self.cookie = None
        self.agent = None
        self.randomAgent = False
        self.level = 1
        self.risk = 1
        self.verbose = 1
        self.batch = False
        self.update = False

class _Kb:
    """Knowledge base container"""
    def __init__(self):
        self.injection = {}
        self.techniques = []
        self.testOnly = False

# Global instances
cmdLineOptions = _CmdLineOptions()
conf = _Conf()
kb = _Kb()