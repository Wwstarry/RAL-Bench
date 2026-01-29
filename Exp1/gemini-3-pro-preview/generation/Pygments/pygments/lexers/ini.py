from pygments.lex import RegexLexer
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation

class IniLexer(RegexLexer):
    name = 'INI'
    aliases = ['ini', 'cfg']
    filenames = ['*.ini', '*.cfg']
    mimetypes = ['text/x-ini']

    tokens = {
        'root': [
            (r'\s+', Text),
            (r'[;#].*', Comment.Single),
            (r'\[.*?\]', Keyword),
            (r'(.*?)([ \t]*)(=)([ \t]*)(.*)', 
             (Name.Attribute, Text, Operator, Text, String)),
        ],
    }