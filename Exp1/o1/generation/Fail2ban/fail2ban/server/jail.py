from .filter import searchIP

class Jail:
    """
    This is a minimal Jail object managing filter logic in a safe, offline manner.
    """

    def __init__(self, name, log_filter=None):
        self.name = name
        self.log_filter = log_filter  # For simplicity, we assume 'log_filter' is a regex or something similar
        self.matched_ips = []

    def processLine(self, line):
        """
        Process a single log line using the filter to search for IPs.
        If an IP is found, store it in matched_ips.
        """
        ip_found = searchIP(line)
        if ip_found:
            # In a real Fail2Ban scenario, we might count repeated failures and ban.
            # Here, we simply store the matched IP for demonstration.
            self.matched_ips.append(ip_found)

    def getMatchedIPs(self):
        """
        Return a list of all matched IPs so far.
        """
        return self.matched_ips