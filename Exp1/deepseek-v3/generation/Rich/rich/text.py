from typing import Any, List, Optional

class Text:
    def __init__(self, text: str = "", style: Optional[str] = None):
        self.text = text
        self.style = style
        
    def __str__(self) -> str:
        """Return the plain text content."""
        return self.text
        
    def __add__(self, other: Any) -> "Text":
        """Concatenate text objects."""
        if isinstance(other, Text):
            return Text(self.text + other.text, self.style)
        elif isinstance(other, str):
            return Text(self.text + other, self.style)
        else:
            return Text(self.text + str(other), self.style)
            
    def __len__(self) -> int:
        """Return the length of the text."""
        return len(self.text)