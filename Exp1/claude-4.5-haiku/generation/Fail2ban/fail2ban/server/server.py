"""Fail2Ban server module."""

from typing import Dict, List
from fail2ban.server.jail import Jail


class Server:
    """
    Fail2Ban server object managing multiple jails.
    """
    
    def __init__(self):
        """Initialize the server."""
        self.jails: Dict[str, Jail] = {}
        self.running = False
    
    def addJail(self, jail: Jail) -> None:
        """
        Add a jail to the server.
        
        Args:
            jail: Jail object to add.
        """
        self.jails[jail.name] = jail
    
    def getJail(self, name: str) -> Jail:
        """
        Get a jail by name.
        
        Args:
            name: Name of the jail.
            
        Returns:
            Jail object.
            
        Raises:
            KeyError: If jail not found.
        """
        return self.jails[name]
    
    def listJails(self) -> List[str]:
        """
        List all jail names.
        
        Returns:
            List of jail names.
        """
        return sorted(list(self.jails.keys()))
    
    def start(self) -> None:
        """Start the server."""
        self.running = True
    
    def stop(self) -> None:
        """Stop the server."""
        self.running = False
    
    def isRunning(self) -> bool:
        """
        Check if server is running.
        
        Returns:
            True if running, False otherwise.
        """
        return self.running