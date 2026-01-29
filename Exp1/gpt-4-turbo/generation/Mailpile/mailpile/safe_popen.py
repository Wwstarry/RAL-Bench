import subprocess
import threading
import os

class SafePopen:
    """
    A safe wrapper around subprocess.Popen that avoids shell injection,
    provides simple pipe helpers, and ensures resources are cleaned up.
    """

    def __init__(self, args, stdin=None, stdout=None, stderr=None, env=None, cwd=None):
        self.args = args
        self.env = env
        self.cwd = cwd
        self._proc = subprocess.Popen(
            args,
            stdin=stdin or subprocess.PIPE,
            stdout=stdout or subprocess.PIPE,
            stderr=stderr or subprocess.PIPE,
            env=env,
            cwd=cwd,
            shell=False,
            close_fds=True
        )

    def communicate(self, input=None, timeout=None):
        """
        Communicate with the process, optionally sending input.
        Returns (stdout, stderr).
        """
        try:
            out, err = self._proc.communicate(input=input, timeout=timeout)
            return out, err
        except subprocess.TimeoutExpired:
            self._proc.kill()
            out, err = self._proc.communicate()
            return out, err

    def wait(self, timeout=None):
        return self._proc.wait(timeout=timeout)

    def poll(self):
        return self._proc.poll()

    def terminate(self):
        self._proc.terminate()

    def kill(self):
        self._proc.kill()

    @property
    def returncode(self):
        return self._proc.returncode

    @property
    def pid(self):
        return self._proc.pid

def safe_popen(args, **kwargs):
    """
    Convenience function to create a SafePopen instance.
    """
    return SafePopen(args, **kwargs)