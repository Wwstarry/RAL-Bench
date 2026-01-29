"""VCard parsing and serialization utilities."""

import re
from typing import List, Dict, Optional, Tuple


class VCardLine:
    """Represents a single line in a VCard."""
    
    def __init__(self, name: str, value: str = '', params: Optional[Dict[str, str]] = None):
        """
        Initialize VCardLine.
        
        Args:
            name: Property name (e.g., 'FN', 'EMAIL')
            value: Property value
            params: Optional parameters dictionary
        """
        self.name = name.upper()
        self.value = value
        self.params = params or {}
    
    def add_param(self, key: str, val: str) -> 'VCardLine':
        """
        Add a parameter to this line.
        
        Args:
            key: Parameter key
            val: Parameter value
            
        Returns:
            Self for chaining
        """
        self.params[key.upper()] = val
        return self
    
    def get_param(self, key: str, default: str = '') -> str:
        """
        Get a parameter value.
        
        Args:
            key: Parameter key
            default: Default value if not found
            
        Returns:
            Parameter value
        """
        return self.params.get(key.upper(), default)
    
    def serialize(self) -> str:
        """
        Serialize to VCard format.
        
        Returns:
            VCard line string
        """
        parts = [self.name]
        
        for key, val in sorted(self.params.items()):
            # Quote value if it contains special characters
            if any(c in val for c in [';', ',', ':']):
                val = f'"{val}"'
            parts.append(f'{key}={val}')
        
        line = ';'.join(parts) + ':' + self.value
        return line
    
    @staticmethod
    def parse(line: str) -> 'VCardLine':
        """
        Parse a VCard line.
        
        Args:
            line: VCard line string
            
        Returns:
            VCardLine instance
        """
        line = line.strip()
        if ':' not in line:
            raise ValueError(f"Invalid VCard line: {line}")
        
        header, value = line.split(':', 1)
        parts = header.split(';')
        name = parts[0].upper()
        
        params = {}
        for part in parts[1:]:
            if '=' in part:
                key, val = part.split('=', 1)
                # Remove quotes if present
                val = val.strip('"')
                params[key.upper()] = val
        
        return VCardLine(name, value, params)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"VCardLine({self.name}, {self.value!r}, {self.params})"
    
    def __eq__(self, other) -> bool:
        """Equality comparison."""
        if not isinstance(other, VCardLine):
            return False
        return (self.name == other.name and 
                self.value == other.value and 
                self.params == other.params)


class VCard:
    """Simple VCard container."""
    
    def __init__(self, version: str = '3.0'):
        """
        Initialize VCard.
        
        Args:
            version: VCard version
        """
        self.version = version
        self.lines: List[VCardLine] = []
    
    def add_line(self, name: str, value: str = '', params: Optional[Dict[str, str]] = None) -> VCardLine:
        """
        Add a line to the VCard.
        
        Args:
            name: Property name
            value: Property value
            params: Optional parameters
            
        Returns:
            The added VCardLine
        """
        line = VCardLine(name, value, params)
        self.lines.append(line)
        return line
    
    def get_lines(self, name: str) -> List[VCardLine]:
        """
        Get all lines with a specific name.
        
        Args:
            name: Property name
            
        Returns:
            List of matching VCardLine instances
        """
        name = name.upper()
        return [line for line in self.lines if line.name == name]
    
    def get_line(self, name: str) -> Optional[VCardLine]:
        """
        Get first line with a specific name.
        
        Args:
            name: Property name
            
        Returns:
            VCardLine instance or None
        """
        lines = self.get_lines(name)
        return lines[0] if lines else None
    
    def serialize(self) -> str:
        """
        Serialize to VCard format.
        
        Returns:
            VCard string
        """
        lines = ['BEGIN:VCARD', f'VERSION:{self.version}']
        for line in self.lines:
            lines.append(line.serialize())
        lines.append('END:VCARD')
        return '\r\n'.join(lines)
    
    @staticmethod
    def parse(text: str) -> 'VCard':
        """
        Parse VCard text.
        
        Args:
            text: VCard text
            
        Returns:
            VCard instance
        """
        lines = text.strip().split('\r\n')
        if not lines[0].startswith('BEGIN:VCARD'):
            raise ValueError("Invalid VCard: missing BEGIN:VCARD")
        
        vcard = VCard()
        for line in lines[1:]:
            if line.startswith('END:VCARD'):
                break
            if line.startswith('VERSION:'):
                vcard.version = line.split(':', 1)[1]
            elif line and not line.startswith('BEGIN:'):
                vcard.lines.append(VCardLine.parse(line))
        
        return vcard