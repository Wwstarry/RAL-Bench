import shlex
from typing import List, Optional


class Command:
    def __init__(self, script: str, stdout: str = '', stderr: str = '', returncode: int = 0):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode

    def __repr__(self):
        return f"Command(script={self.script!r}, stdout={self.stdout!r}, stderr={self.stderr!r}, returncode={self.returncode!r})"

    def script_parts(self) -> List[str]:
        try:
            return shlex.split(self.script)
        except Exception:
            # fallback naive split
            return self.script.split()