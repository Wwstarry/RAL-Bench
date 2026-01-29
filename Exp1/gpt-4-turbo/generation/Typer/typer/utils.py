import sys

def echo(message="", *, err=False, nl=True):
    stream = sys.stderr if err else sys.stdout
    end = "\n" if nl else ""
    print(message, file=stream, end=end)