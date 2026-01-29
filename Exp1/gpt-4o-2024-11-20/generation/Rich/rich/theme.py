# rich/theme.py

class Theme:
    def __init__(self, styles=None):
        self.styles = styles or {}

    def apply_style(self, text, style):
        if style in self.styles:
            return f"[{style}]{text}[/{style}]"
        return text