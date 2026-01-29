# mailpile.vcard
#
# Simplified VCard parsing logic for benchmarking.
# Focuses on parsing a single VCard line.

import re

class VCardLine(object):
    """
    Represents a single line in a VCard.
    
    Parses a line like: `KEY;PARAM1=val1,val2;PARAM2=val3:VALUE`
    """
    # Regex to split the line into key/params and value
    LINE_RE = re.compile(r'([^:]+):(.*)')
    
    def __init__(self, line):
        self.raw = line.strip()
        self.key = ''
        self.value = ''
        self.params = {}
        self._parse()

    def _parse(self):
        match = self.LINE_RE.match(self.raw)
        if not match:
            # Handle lines without a colon (e.g., BEGIN:VCARD)
            self.key = self.raw
            return

        key_part, self.value = match.groups()
        parts = key_part.split(';')
        self.key = parts[0].upper()

        for param_part in parts[1:]:
            if '=' in param_part:
                param_key, param_val = param_part.split('=', 1)
                # Parameter values can be comma-separated lists
                self.params[param_key.upper()] = param_val.split(',')
            else:
                # Handle parameters without values (e.g., TYPE=PREF)
                # For simplicity, we treat them as keys with a list containing themselves.
                self.params[param_key.upper()] = [param_key.upper()]

    def __str__(self):
        """Serializes the VCardLine back to its string representation."""
        key_part = [self.key]
        for p_key, p_vals in sorted(self.params.items()):
            key_part.append(f"{p_key}={','.join(p_vals)}")
        
        if self.value:
            return f"{';'.join(key_part)}:{self.value}"
        else:
            return ';'.join(key_part)

    def __repr__(self):
        return f"<VCardLine key='{self.key}' value='{self.value}'>"