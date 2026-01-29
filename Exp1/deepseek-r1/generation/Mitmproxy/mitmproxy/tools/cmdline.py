import argparse

def mitmdump():
    parser = argparse.ArgumentParser(description="mitmdump: command-line version of mitmproxy")
    parser.add_argument("--version", action="store_true", help="show version")
    parser.add_argument("-q", "--quiet", action="store_true", help="quiet")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")
    return parser