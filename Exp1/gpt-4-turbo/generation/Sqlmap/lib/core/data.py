class _CmdLineOptions:
    pass

class _Conf:
    def __init__(self):
        self.initialized = False
        self.options = {}

class _Kb:
    def __init__(self):
        self.notes = {}

cmdLineOptions = _CmdLineOptions()
conf = _Conf()
kb = _Kb()