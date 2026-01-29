from pygments.util import get_bool_opt

class TerminalFormatter:
    """
    A formatter that outputs ANSI-colored text for terminals.
    """
    def __init__(self, **options):
        self.use_colors = get_bool_opt(options, "use_colors", True)

    def format(self, tokens):
        if not self.use_colors:
            return "".join(value for _, value in tokens)

        color_map = {
            "Text": "\033[0m",
            "Keyword": "\033[34m",
            "Name": "\033[32m",
            "String": "\033[33m",
            "Number": "\033[31m",
            "Operator": "\033[35m",
            "Punctuation": "\033[90m",
            "Comment": "\033[32m",
            "Error": "\033[41m",
            "Whitespace": "\033[37m",
        }

        result = []
        for token_type, value in tokens:
            color = color_map.get(token_type, "\033[0m")
            result.append(f"{color}{value}\033[0m")
        return "".join(result)