from ..token import Token, Comment, Keyword, Name, String, Number, Operator, Punctuation, Generic, Whitespace

class DefaultStyle:
    """
    Minimal default style definitions.
    """
    styles = {
        Token.Text: "",
        Token.Error: "border: #FF0000",
        Whitespace: "",
        Comment: "italic #408080",
        Keyword: "bold #008000",
        Name: "",
        String: "#BA2121",
        Number: "#1E90FF",
        Operator: "#AA22FF",
        Punctuation: "",
        Generic: "",
    }