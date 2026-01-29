from typing import Dict

class Theme:
    def __init__(self, styles: Dict[str, str] = None):
        self.styles = styles or {}