"""
Logging functionality
"""

import sys


class Logger:
    """
    Simple logger class
    """
    def __init__(self):
        pass
    
    def info(self, msg):
        """Log info message"""
        print("[*] %s" % msg)
    
    def warning(self, msg):
        """Log warning message"""
        print("[!] %s" % msg)
    
    def error(self, msg):
        """Log error message"""
        print("[!] %s" % msg)
    
    def critical(self, msg):
        """Log critical message"""
        print("[CRITICAL] %s" % msg)
        sys.exit(1)


LOGGER = Logger()