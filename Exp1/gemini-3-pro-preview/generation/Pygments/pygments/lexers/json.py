from pygments.lex import RegexLexer
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Literal

class JsonLexer(RegexLexer):
    name = 'JSON'
    aliases = ['json']
    filenames = ['*.json']
    mimetypes = ['application/json']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'[{]\}[\],]', Punctuation),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r'(true|false|null)\b', Keyword.Constant),
            (r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?', Number),
            (r':', Punctuation),
        ],
    }