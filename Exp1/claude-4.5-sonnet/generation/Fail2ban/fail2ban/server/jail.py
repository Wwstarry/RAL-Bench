"""
Jail management for Fail2Ban
"""

from fail2ban.server.filter import Filter


class Jail:
    """
    Jail object managing filter and actions coordination.
    
    A jail monitors a specific service (e.g., sshd) and coordinates
    between the filter (log parsing) and actions (banning).
    """
    
    def __init__(self, name, backend='auto'):
        self.name = name
        self.backend = backend
        self.filter = Filter(name)
        self.actions = []
        self.enabled = False
        self.max_retry = 5
        self.find_time = 600
        self.ban_time = 600
        self.log_path = []
    
    def setEnabled(self, enabled):
        """Enable or disable the jail"""
        self.enabled = enabled
    
    def isEnabled(self):
        """Check if jail is enabled"""
        return self.enabled
    
    def setMaxRetry(self, max_retry):
        """Set maximum retry count before banning"""
        self.max_retry = max_retry
        self.filter.max_retry = max_retry
    
    def getMaxRetry(self):
        """Get maximum retry count"""
        return self.max_retry
    
    def setFindTime(self, find_time):
        """Set time window for counting failures"""
        self.find_time = find_time
        self.filter.find_time = find_time
    
    def getFindTime(self):
        """Get find time"""
        return self.find_time
    
    def setBanTime(self, ban_time):
        """Set ban duration"""
        self.ban_time = ban_time
    
    def getBanTime(self):
        """Get ban time"""
        return self.ban_time
    
    def addLogPath(self, path):
        """Add a log file path to monitor"""
        if path not in self.log_path:
            self.log_path.append(path)
    
    def getLogPath(self):
        """Get list of log paths"""
        return self.log_path
    
    def addFailRegex(self, regex):
        """Add a failure regex pattern to the filter"""
        self.filter.addFailRegex(regex)
    
    def addIgnoreRegex(self, regex):
        """Add an ignore regex pattern to the filter"""
        self.filter.addIgnoreRegex(regex)
    
    def addAction(self, action):
        """Add an action to execute on ban"""
        self.actions.append(action)
    
    def getActions(self):
        """Get list of actions"""
        return self.actions
    
    def processLine(self, line):
        """
        Process a log line through the filter.
        
        Args:
            line: Log line to process
            
        Returns:
            List of IPs to ban
        """
        return self.filter.processLine(line)
    
    def getFilter(self):
        """Get the jail's filter"""
        return self.filter
    
    def getName(self):
        """Get jail name"""
        return self.name