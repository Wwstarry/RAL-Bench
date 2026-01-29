from pygments.lexers.python import PythonLexer
from pygments.lexers.json import JsonLexer
from pygments.lexers.ini import IniLexer

def get_lexer_by_name(name):
    """
    Get a lexer instance by its name.

    :param name: The name of the lexer.
    :return: An instance of the corresponding lexer.
    """
    lexers = {
        "python": PythonLexer,
        "json": JsonLexer,
        "ini": IniLexer,
    }
    lexer_cls = lexers.get(name.lower())
    if lexer_cls is None:
        raise ValueError(f"No lexer found for name: {name}")
    return lexer_cls()