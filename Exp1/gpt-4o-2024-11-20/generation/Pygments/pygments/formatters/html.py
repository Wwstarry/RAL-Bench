class HtmlFormatter:
    """
    A formatter that outputs HTML.
    """
    def format(self, tokens):
        result = []
        for token_type, value in tokens:
            result.append(f"<span class='{token_type}'>{value}</span>")
        return "".join(result)

    def get_style_defs(self):
        return """
        .Text { color: black; }
        .Keyword { color: blue; font-weight: bold; }
        .Name { color: green; }
        .String { color: orange; }
        .Number { color: red; }
        .Operator { color: purple; }
        .Punctuation { color: gray; }
        .Comment { color: darkgreen; font-style: italic; }
        .Error { color: red; background-color: yellow; }
        .Whitespace { color: #ccc; }
        """