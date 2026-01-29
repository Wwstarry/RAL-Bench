from typing import Dict, Optional

class Theme:
    def __init__(self, styles: Optional[Dict[str, str]] = None):
        self.styles = styles or {}

    def get(self, style: str) -> Optional[str]:
        return self.styles.get(style)

    def __getitem__(self, style: str) -> Optional[str]:
        return self.get(style)