"""
Configuration file reader for Fail2Ban
"""

import configparser
import os


class ConfigReader:
    """
    Read and parse Fail2Ban configuration files.
    """
    
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config_files = []
    
    def read(self, filename):
        """
        Read a configuration file.
        
        Args:
            filename: Path to config file
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(filename):
            return False
        
        try:
            self.config.read(filename)
            self.config_files.append(filename)
            return True
        except Exception:
            return False
    
    def getSections(self):
        """Get list of sections in config"""
        return self.config.sections()
    
    def getOptions(self, section):
        """Get options for a section"""
        if section in self.config:
            return dict(self.config[section])
        return {}
    
    def get(self, section, option, fallback=None):
        """Get a configuration value"""
        return self.config.get(section, option, fallback=fallback)
    
    def getint(self, section, option, fallback=None):
        """Get an integer configuration value"""
        return self.config.getint(section, option, fallback=fallback)
    
    def getboolean(self, section, option, fallback=None):
        """Get a boolean configuration value"""
        return self.config.getboolean(section, option, fallback=fallback)