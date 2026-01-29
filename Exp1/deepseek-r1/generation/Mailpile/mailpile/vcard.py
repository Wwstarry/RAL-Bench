"""VCard parsing and serialization."""
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

@dataclass
class VCardLine:
    """Represents a single VCard line."""
    group: Optional[str] = None
    name: str = ""
    params: Dict[str, List[str]] = field(default_factory=dict)
    value: str = ""
    
    def __str__(self) -> str:
        """Serialize VCard line to string."""
        parts = []
        if self.group:
            parts.append(f"{self.group}.")
        parts.append(self.name)
        
        for param_name, param_values in self.params.items():
            if param_values:
                values = ','.join(param_values)
                parts.append(f";{param_name}={values}")
        
        parts.append(f":{self.value}")
        return ''.join(parts)
        
    @classmethod
    def parse(cls, line: str) -> 'VCardLine':
        """Parse VCard line from string."""
        line = line.strip()
        if not line:
            raise ValueError("Empty line cannot be parsed as VCard")
            
        # Split into name+params and value
        if ':' not in line:
            raise ValueError("Invalid VCard line: missing colon")
            
        name_part, value = line.split(':', 1)
        
        # Check for group prefix
        group = None
        if '.' in name_part:
            group, name_part = name_part.split('.', 1)
            
        # Split parameters
        name_parts = name_part.split(';')
        name = name_parts[0]
        params = {}
        
        for param in name_parts[1:]:
            if '=' in param:
                param_name, param_value = param.split('=', 1)
                params[param_name.upper()] = param_value.split(',')
            else:
                params[param.upper()] = []
                
        return cls(group=group, name=name.upper(), params=params, value=value)
        
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get parameter value."""
        return self.params.get(name.upper(), default)
        
    def add_param(self, name: str, value: str) -> None:
        """Add parameter to line."""
        name = name.upper()
        if name not in self.params:
            self.params[name] = []
        if value not in self.params[name]:
            self.params[name].append(value)
            
    def remove_param(self, name: str, value: Optional[str] = None) -> bool:
        """Remove parameter or specific value from parameter."""
        name = name.upper()
        if name not in self.params:
            return False
            
        if value is None:
            del self.params[name]
            return True
        elif value in self.params[name]:
            self.params[name].remove(value)
            if not self.params[name]:
                del self.params[name]
            return True
        return False

class VCard:
    """VCard parser and serializer."""
    
    def __init__(self):
        self.lines: List[VCardLine] = []
        
    @classmethod
    def parse(cls, data: str) -> 'VCard':
        """Parse VCard data from string."""
        vcard = cls()
        lines = data.strip().split('\n')
        
        # Handle folded lines (lines starting with space or tab)
        unfolded_lines = []
        current_line = ""
        
        for line in lines:
            if line.startswith((' ', '\t')):
                current_line += line[1:]
            else:
                if current_line:
                    unfolded_lines.append(current_line)
                current_line = line
        if current_line:
            unfolded_lines.append(current_line)
            
        for line in unfolded_lines:
            if line:
                vcard.lines.append(VCardLine.parse(line))
                
        return vcard
        
    def serialize(self) -> str:
        """Serialize VCard to string."""
        lines = []
        for vcard_line in self.lines:
            line_str = str(vcard_line)
            # Fold long lines (max 75 chars)
            while len(line_str) > 75:
                lines.append(line_str[:75])
                line_str = ' ' + line_str[75:]
            lines.append(line_str)
        return '\n'.join(lines) + '\n'
        
    def add_line(self, line: VCardLine) -> None:
        """Add VCard line."""
        self.lines.append(line)
        
    def get_lines(self, name: Optional[str] = None) -> List[VCardLine]:
        """Get all lines or lines with specific name."""
        if name is None:
            return self.lines.copy()
        return [line for line in self.lines if line.name == name.upper()]
        
    def get_values(self, name: str) -> List[str]:
        """Get values for lines with specific name."""
        return [line.value for line in self.get_lines(name)]
        
    def get_first_value(self, name: str, default: str = "") -> str:
        """Get first value for lines with specific name."""
        values = self.get_values(name)
        return values[0] if values else default
        
    def remove_lines(self, name: str) -> int:
        """Remove all lines with specific name."""
        initial_count = len(self.lines)
        self.lines = [line for line in self.lines if line.name != name.upper()]
        return initial_count - len(self.lines)