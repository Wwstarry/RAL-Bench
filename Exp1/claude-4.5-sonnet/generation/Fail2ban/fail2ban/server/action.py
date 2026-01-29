"""
Action management for Fail2Ban
"""


class Action:
    """
    Base action class for executing ban/unban operations.
    
    In this safe implementation, actions are logged but not executed.
    """
    
    def __init__(self, name):
        self.name = name
        self.ban_list = []
    
    def ban(self, ip):
        """
        Ban an IP address (safe implementation - no actual firewall changes).
        
        Args:
            ip: IP address to ban
        """
        if ip not in self.ban_list:
            self.ban_list.append(ip)
            return True
        return False
    
    def unban(self, ip):
        """
        Unban an IP address (safe implementation).
        
        Args:
            ip: IP address to unban
        """
        if ip in self.ban_list:
            self.ban_list.remove(ip)
            return True
        return False
    
    def getBanned(self):
        """Get list of banned IPs"""
        return self.ban_list.copy()
    
    def getName(self):
        """Get action name"""
        return self.name