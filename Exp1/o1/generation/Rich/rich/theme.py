class Style:
    """
    Minimal representation of a textual Style,
    storing only a foreground color name for simplicity.
    """

    def __init__(self, color=None):
        self.color = color

    def to_ansi(self):
        """Convert style to an ANSI code, if recognized."""
        COLOR_MAP = {
            "black": 30, "red": 31, "green": 32, "yellow": 33,
            "blue": 34, "magenta": 35, "cyan": 36, "white": 37,
            "bright_black": 90, "bright_red": 91, "bright_green": 92,
            "bright_yellow": 93, "bright_blue": 94,
            "bright_magenta": 95, "bright_cyan": 96, "bright_white": 97,
        }
        if self.color in COLOR_MAP:
            return f"\033[{COLOR_MAP[self.color]}m"
        return ""


class Theme:
    """
    A theme is a collection of named styles.
    """

    def __init__(self, styles=None):
        # styles is dict of str -> Style
        self.styles = styles if styles else {}

    def add_style(self, name: str, style: Style):
        self.styles[name] = style