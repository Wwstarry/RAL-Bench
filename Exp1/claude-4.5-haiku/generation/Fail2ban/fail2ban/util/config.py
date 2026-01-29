"""Configuration parsing utilities."""

import configparser
from typing import Dict, List, Optional


class ConfigParser:
    """
    Parser for Fail2Ban configuration files.
    """
    
    def __init__(self):
        """Initialize the config parser."""
        self.config = configparser.ConfigParser()
    
    def read(self, filename: str) -> None:
        """
        Read configuration file.
        
        Args:
            filename: Path to configuration file.
        """
        self.config.read(filename)
    
    def getSections(self) -> List[str]:
        """
        Get all sections in configuration.
        
        Returns:
            List of section names.
        """
        return self.config.sections()
    
    def getOptions(self, section: str) -> List[str]:
        """
        Get all options in a section.
        
        Args:
            section: Section name.
            
        Returns:
            List of option names.
        """
        if self.config.has_section(section):
            return self.config.options(section)
        return []
    
    def get(self, section: str, option: str, fallback: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value.
        
        Args:
            section: Section name.
            option: Option name.
            fallback: Fallback value if not found.
            
        Returns:
            Configuration value or fallback.
        """
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def getint(self, section: str, option: str, fallback: Optional[int] = None) -> Optional[int]:
        """
        Get an integer configuration value.
        
        Args:
            section: Section name.
            option: Option name.
            fallback: Fallback value if not found.
            
        Returns:
            Integer configuration value or fallback.
        """
        try:
            return self.config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def getboolean(self, section: str, option: str, fallback: Optional[bool] = None) -> Optional[bool]:
        """
        Get a boolean configuration value.
        
        Args:
            section: Section name.
            option: Option name.
            fallback: Fallback value if not found.
            
        Returns:
            Boolean configuration value or fallback.
        """
        try:
            return self.config.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback