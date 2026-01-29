# rich/text.py

class Text:
    def __init__(self, content, style=None):
        self.content = content
        self.style = style

    def render(self):
        if self.style:
            return f"[{self.style}]{self.content}[/{self.style}]"
        return self.content