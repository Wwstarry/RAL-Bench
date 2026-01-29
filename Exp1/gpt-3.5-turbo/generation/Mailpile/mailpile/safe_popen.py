import subprocess
import threading
import os


class SafePopen:
    """
    A safe subprocess wrapper that avoids common pitfalls with pipes and subprocesses.
    """

    def __init__(self, args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, env=None):
        self.args = args
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.shell = shell
        self.env = env
        self.process = None

    def __enter__(self):
        self.process = subprocess.Popen(
            self.args,
            stdin=self.stdin,
            stdout=self.stdout,
            stderr=self.stderr,
            shell=self.shell,
            env=self.env,
            close_fds=True
        )
        return self.process

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.process:
            try:
                self.process.terminate()
            except Exception:
                pass
            self.process.wait()


def pipe_reader(pipe, callback):
    """
    Reads from a pipe in a separate thread and calls callback with each line.
    """
    def run():
        with pipe:
            for line in iter(pipe.readline, b''):
                callback(line)
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread