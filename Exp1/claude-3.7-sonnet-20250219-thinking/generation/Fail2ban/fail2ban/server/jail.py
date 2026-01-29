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

import logging
import time

from .filter import Filter
from .actions import Actions

# Logger
log = logging.getLogger(__name__)

class Jail(object):
    """Handles coordination between filter and actions.
    
    This class is responsible for managing the filter that detects failures
    and the actions that are taken when failures are detected.
    """
    
    def __init__(self, name):
        self.name = name
        self.filter = Filter(self)
        self.actions = Actions()
        self._isActive = False
        self._banned = {}  # IP -> (timestamp, failures)
        
    def start(self):
        """Start the jail."""
        if not self._isActive:
            self._isActive = True
            log.info("Jail %r started", self.name)
            
    def stop(self):
        """Stop the jail."""
        if self._isActive:
            self._isActive = False
            log.info("Jail %r stopped", self.name)
            
    def isActive(self):
        """Check if the jail is active.
        
        Returns:
            bool: True if the jail is active, False otherwise.
        """
        return self._isActive
        
    def setFindTime(self, findTime):
        """Set the find time.
        
        Args:
            findTime (int): Find time in seconds.
        """
        self.filter.findTime = findTime
        
    def setMaxRetry(self, maxRetry):
        """Set the maximum number of retries.
        
        Args:
            maxRetry (int): Maximum number of retries.
        """
        self.filter.maxRetry = maxRetry
        
    def setBanTime(self, banTime):
        """Set the ban time.
        
        Args:
            banTime (int): Ban time in seconds.
        """
        self.filter.banTime = banTime
        
    def addFailRegex(self, regex):
        """Add a failure regex pattern.
        
        Args:
            regex (str): Regular expression pattern to match failures.
        """
        self.filter.addFailRegex(regex)
        
    def addIgnoreRegex(self, regex):
        """Add an ignore regex pattern.
        
        Args:
            regex (str): Regular expression pattern to ignore.
        """
        self.filter.addIgnoreRegex(regex)
        
    def getFailures(self):
        """Get the number of failures.
        
        Returns:
            dict: Dictionary mapping IPs to failure counts.
        """
        failures = {}
        for ip, times in self.filter.failManager._failures.items():
            failures[ip] = len(times)
        return failures
        
    def getBanned(self):
        """Get the banned IPs.
        
        Returns:
            dict: Dictionary mapping banned IPs to ban information.
        """
        return dict(self._banned)
        
    def ban(self, ip, failures):
        """Ban an IP address.
        
        Args:
            ip (str): IP address to ban.
            failures (int): Number of failures that triggered the ban.
        """
        if ip in self._banned:
            return
            
        self._banned[ip] = (time.time(), failures)
        log.info("[%s] Ban %s", self.name, ip)
        
        if self._isActive:
            # Execute actions (in a real implementation, this would update firewall)
            # In this safe implementation, we just log the ban
            self.actions.ban(ip)
            
    def unban(self, ip):
        """Unban an IP address.
        
        Args:
            ip (str): IP address to unban.
        """
        if ip not in self._banned:
            return False
            
        del self._banned[ip]
        log.info("[%s] Unban %s", self.name, ip)
        
        if self._isActive:
            # Execute actions (in a real implementation, this would update firewall)
            # In this safe implementation, we just log the unban
            self.actions.unban(ip)
            
        return True
        
    def processLine(self, line, date=None):
        """Process a log line.
        
        Args:
            line (str): Line to process.
            date (float, optional): Timestamp of the log line. Defaults to now.
            
        Returns:
            list: List of match information dictionaries.
        """
        if not self._isActive:
            return []
            
        return self.filter.processLine(line, date)