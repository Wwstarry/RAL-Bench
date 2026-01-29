# This file is part of Fail2Ban.
#
# Fail2Ban is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Fail2Ban is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Fail2Ban; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

__author__ = "Fail2Ban Contributors"
__copyright__ = "Copyright (c) 2004-2008 Cyril Jaquier, 2008- Fail2Ban Contributors"
__license__ = "GPL"

import re
import os
import time
import logging

# IPv4 and IPv6 regular expressions
IPV4_REGEX = r"(?:\d{1,3}\.){3}\d{1,3}"
IPV6_REGEX = r"(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}"
IPV6_COMPRESSED_REGEX = r"(?:(?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*)?)::" \
                        r"(?:(?:[0-9a-fA-F]{1,4}(?::[0-9a-fA-F]{1,4})*)?)"

# IP address regular expressions
IP_REGEX = r"(?:" + IPV4_REGEX + r")|(?:" + IPV6_REGEX + r")|(?:" + IPV6_COMPRESSED_REGEX + r")"

# Logger
log = logging.getLogger(__name__)

def isValidIP(ip):
    """Check if the given string is a valid IP address.
    
    Args:
        ip (str): The IP address to validate.
        
    Returns:
        bool: True if the IP is valid, False otherwise.
    """
    return bool(re.match(r"^" + IP_REGEX + r"$", ip))

def searchIP(text):
    """Search for IPs in the given text.
    
    Args:
        text (str): Text to search in.
        
    Returns:
        list: List of IPs found in the text.
    """
    return re.findall(r"(?<![\d\.:])(?:\b" + IP_REGEX + r"\b)", text)

class Filter(object):
    """Base class for filters that match log entries against patterns.
    
    This class handles the core functions of filtering log files for patterns
    and extracting IP addresses from matches.
    """
    
    def __init__(self, jail=None):
        self.jail = jail
        self.failRegex = []
        self.ignoreRegex = []
        self._failRegexCompiled = []
        self._ignoreRegexCompiled = []
        self.findTime = 600  # 10 minutes
        self.banTime = 600   # 10 minutes
        self.maxRetry = 3
        self.failManager = FailManager()
        
    def addFailRegex(self, regex):
        """Add a failure regex pattern.
        
        Args:
            regex (str): Regular expression pattern to match failures.
        """
        try:
            compiled = re.compile(regex)
            self.failRegex.append(regex)
            self._failRegexCompiled.append(compiled)
        except re.error as e:
            log.error("Failed to compile regex %r: %s", regex, e)
            
    def addIgnoreRegex(self, regex):
        """Add an ignore regex pattern.
        
        Args:
            regex (str): Regular expression pattern to ignore.
        """
        try:
            compiled = re.compile(regex)
            self.ignoreRegex.append(regex)
            self._ignoreRegexCompiled.append(compiled)
        except re.error as e:
            log.error("Failed to compile regex %r: %s", regex, e)
            
    def processLine(self, line, date=None):
        """Process a single line of log file.
        
        Args:
            line (str): Line from log file.
            date (float, optional): Timestamp of the log line. Defaults to now.
            
        Returns:
            list: List of match information dictionaries.
        """
        if date is None:
            date = time.time()
            
        matches = []
        
        # Try to match line with ignore patterns
        ignored = False
        for ignoreRegex in self._ignoreRegexCompiled:
            if ignoreRegex.search(line):
                ignored = True
                break
                
        # If not ignored, try to match with failure patterns
        if not ignored:
            for failRegexIndex, failRegex in enumerate(self._failRegexCompiled):
                match = failRegex.search(line)
                if match:
                    # Extract IP addresses from the match
                    ips = searchIP(match.group())
                    if not ips:
                        continue
                        
                    ip = ips[0]
                    if not isValidIP(ip):
                        continue
                        
                    matches.append({
                        'ip': ip,
                        'time': date,
                        'pattern': self.failRegex[failRegexIndex]
                    })
                    
                    # Add to fail manager
                    self.failManager.addFailure(ip, date)
                    
                    # Check if we need to ban this IP
                    failures = self.failManager.getFailures(ip)
                    if failures >= self.maxRetry and self.jail is not None:
                        self.jail.ban(ip, failures)
                        
        return matches
        
class FailManager(object):
    """Handles tracking failures for IP addresses."""
    
    def __init__(self):
        self._failures = {}
        
    def addFailure(self, ip, time):
        """Add a failure for the given IP address.
        
        Args:
            ip (str): The IP address.
            time (float): Timestamp of the failure.
        """
        if ip not in self._failures:
            self._failures[ip] = []
        self._failures[ip].append(time)
        
    def getFailures(self, ip):
        """Get the number of failures for the given IP.
        
        Args:
            ip (str): The IP address.
            
        Returns:
            int: Number of failures for the IP.
        """
        if ip not in self._failures:
            return 0
        return len(self._failures[ip])
        
    def cleanupOldFailures(self, time, findTime):
        """Remove failures older than findTime seconds.
        
        Args:
            time (float): Current timestamp.
            findTime (int): Number of seconds to look back.
        """
        for ip in list(self._failures.keys()):
            self._failures[ip] = [t for t in self._failures[ip] if time - t <= findTime]
            if not self._failures[ip]:
                del self._failures[ip]