class Settings(object):
    def __init__(self):
        self.rules = None
        self.exclude_rules = []
        self.wait_command = 3
        self.require_confirmation = False  # Default to False for unattended tests
        self.no_colors = False
        self.priority = {}
        self.history_limit = None
        self.alter_history = True
        self.instant_mode = False
        self.repeat = False
        self.debug = False
        self.env = {'LC_ALL': 'C', 'LANG': 'C', 'GIT_TRACE': '1'}

    def init(self, args=None):
        pass

settings = Settings()