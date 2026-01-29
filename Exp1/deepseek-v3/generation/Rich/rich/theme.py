from typing import Dict, Optional

class Theme:
    def __init__(self, styles: Optional[Dict[str, str]] = None):
        self.styles = styles or {}
        
    def get_style(self, name: str) -> Optional[str]:
        """Get a style by name."""
        return self.styles.get(name)