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

# Logger
log = logging.getLogger(__name__)

class Actions(object):
    """Handles actions to be taken when failures are detected.
    
    This class is responsible for executing actions when failures are detected.
    In this safe implementation, we just log the ban/unban operations without
    actually modifying any firewall rules.
    """
    
    def __init__(self):
        self._actions = []
        
    def ban(self, ip):
        """Ban an IP address.
        
        In a real implementation, this would update firewall rules.
        In this safe version, it just logs the ban.
        
        Args:
            ip (str): IP address to ban.
        """
        log.info("Would ban %s (safe mode - no actual firewall changes)", ip)
        
    def unban(self, ip):
        """Unban an IP address.
        
        In a real implementation, this would update firewall rules.
        In this safe version, it just logs the unban.
        
        Args:
            ip (str): IP address to unban.
        """
        log.info("Would unban %s (safe mode - no actual firewall changes)", ip)