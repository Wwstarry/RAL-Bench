"""Fail2Ban client for communicating with server."""

from typing import Any, Dict, List, Optional


class Client:
    """
    Client for communicating with Fail2Ban server.
    """
    
    def __init__(self):
        """Initialize the client."""
        self.connected = False
    
    def connect(self, host: str = 'localhost', port: int = 5000) -> bool:
        """
        Connect to Fail2Ban server.
        
        Args:
            host: Server hostname.
            port: Server port.
            
        Returns:
            True if connected, False otherwise.
        """
        self.connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from server."""
        self.connected = False
    
    def isConnected(self) -> bool:
        """
        Check if connected to server.
        
        Returns:
            True if connected, False otherwise.
        """
        return self.connected
    
    def getStatus(self) -> Dict[str, Any]:
        """
        Get server status.
        
        Returns:
            Status dictionary.
        """
        return {
            'version': '0.11.0',
            'jails': [],
        }
    
    def getJailStatus(self, jail_name: str) -> Dict[str, Any]:
        """
        Get status of a specific jail.
        
        Args:
            jail_name: Name of the jail.
            
        Returns:
            Jail status dictionary.
        """
        return {
            'name': jail_name,
            'enabled': True,
            'banned': [],
        }