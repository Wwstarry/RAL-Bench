class Text:
    """
    Minimal Text container that can store styled content.
    For simplicity, store as raw text with optional style markup.
    """

    def __init__(self, text: str = "", style: str = None):
        self.text = text
        self.style = style

    @property
    def plain(self):
        """Return the raw text (with no markup brackets) for console usage."""
        return self.text

    def __str__(self):
        return self.text

    def append(self, text: str, style: str = None):
        """
        Append more text. If style is given, wrap it in markup bracket.
        """
        if style:
            self.text += f"[{style}]{text}[/{style}]"
        else:
            self.text += text