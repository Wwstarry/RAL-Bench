class VCardLine:
    """
    Represents a single line in a VCard file.
    Format: NAME;PARAM=VAL:VALUE
    """
    def __init__(self, name, value, params=None, group=None):
        self.name = name.upper()
        self.value = value
        self.params = params or {}
        self.group = group

    def __str__(self):
        parts = []
        if self.group:
            parts.append(f"{self.group}.")
        parts.append(self.name)
        
        for k, v in sorted(self.params.items()):
            # Simple escaping for parameter values could be added here
            parts.append(f";{k.upper()}={v}")
            
        parts.append(f":{self.value}")
        return "".join(parts)

    @classmethod
    def parse(cls, line):
        """
        Parses a VCard line string into a VCardLine object.
        """
        line = line.strip()
        if not line:
            return None
            
        # Split into meta and value
        if ':' not in line:
            return None # Invalid line
            
        meta_part, value = line.split(':', 1)
        
        # Handle grouping (e.g., item1.EMAIL)
        group = None
        if '.' in meta_part:
            possible_group, rest = meta_part.split('.', 1)
            # Check if the split part is just the name or a group
            # Simplified logic: if there are no semicolons in the first part, it's a group
            if ';' not in possible_group:
                group = possible_group
                meta_part = rest

        # Split name and params
        parts = meta_part.split(';')
        name = parts[0]
        params = {}
        
        for p in parts[1:]:
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = v
            else:
                # Parameter without value (e.g. PREF)
                params[p] = None
                
        return cls(name, value, params=params, group=group)

def ParseVCard(vcard_data):
    """
    Parses a block of VCard text into a list of VCardLine objects.
    Handles line unfolding.
    """
    lines = []
    current_line = ""
    
    # Unfold lines
    for raw_line in vcard_data.splitlines():
        if raw_line.startswith(" ") or raw_line.startswith("\t"):
            current_line += raw_line[1:]
        else:
            if current_line:
                obj = VCardLine.parse(current_line)
                if obj: lines.append(obj)
            current_line = raw_line
            
    if current_line:
        obj = VCardLine.parse(current_line)
        if obj: lines.append(obj)
        
    return lines