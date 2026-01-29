"""
Jail configuration reader
"""

from fail2ban.client.configreader import ConfigReader
from fail2ban.server.jail import Jail


class JailReader:
    """
    Read jail configurations and create Jail objects.
    """
    
    def __init__(self, jail_name):
        self.jail_name = jail_name
        self.config = ConfigReader()
        self.jail = None
    
    def read(self, config_file):
        """
        Read jail configuration from file.
        
        Args:
            config_file: Path to jail.conf or jail.local
            
        Returns:
            True if successful
        """
        if not self.config.read(config_file):
            return False
        
        # Create jail if section exists
        if self.jail_name in self.config.getSections():
            self.jail = Jail(self.jail_name)
            options = self.config.getOptions(self.jail_name)
            
            # Apply configuration
            if 'enabled' in options:
                enabled = self.config.getboolean(self.jail_name, 'enabled', fallback=False)
                self.jail.setEnabled(enabled)
            
            if 'maxretry' in options:
                max_retry = self.config.getint(self.jail_name, 'maxretry', fallback=5)
                self.jail.setMaxRetry(max_retry)
            
            if 'findtime' in options:
                find_time = self.config.getint(self.jail_name, 'findtime', fallback=600)
                self.jail.setFindTime(find_time)
            
            if 'bantime' in options:
                ban_time = self.config.getint(self.jail_name, 'bantime', fallback=600)
                self.jail.setBanTime(ban_time)
            
            if 'logpath' in options:
                log_path = self.config.get(self.jail_name, 'logpath')
                if log_path:
                    for path in log_path.split('\n'):
                        path = path.strip()
                        if path:
                            self.jail.addLogPath(path)
            
            return True
        
        return False
    
    def getJail(self):
        """Get the configured Jail object"""
        return self.jail