import sys
from lib.core.datatype import AttribDict

class KnowledgeBase(AttribDict):
    def __init__(self, *args, **kwargs):
        super(KnowledgeBase, self).__init__(*args, **kwargs)

# Command line options
cmdLineOptions = AttribDict()

# Configuration object
conf = AttribDict()

# Knowledge Base object
kb = KnowledgeBase()

# A dummy logger class to avoid import errors and provide basic output
class Logger:
    def _write(self, level, msg):
        # In a real tool, this would write to a log file and/or console
        # with different formatting. For this mock, we just print.
        if level == "CRITICAL":
            print(f"[{level}] {msg}", file=sys.stderr)
        else:
            print(f"[{level}] {msg}")

    def critical(self, msg):
        self._write("CRITICAL", msg)

    def error(self, msg):
        self._write("ERROR", msg)

    def info(self, msg):
        self._write("INFO", msg)

    def debug(self, msg):
        # In this mock, debug messages are ignored
        pass

logger = Logger()