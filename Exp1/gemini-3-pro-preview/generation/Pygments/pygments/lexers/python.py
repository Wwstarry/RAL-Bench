from pygments.lex import RegexLexer
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation

class PythonLexer(RegexLexer):
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py', '*.pyw', '*.sc', 'SConstruct', 'SConscript', '*.tac', '*.sage']
    mimetypes = ['text/x-python', 'application/x-python']

    tokens = {
        'root': [
            (r'\n', Text),
            (r'^(\s*)([rR]?u?|u[rR]?|U[rR]?|b[rR]?|B[rR]?)("""(?:.|\n)*?""")',
             (Text, String.Doc)),
            (r"^(\s*)([rR]?u?|u[rR]?|U[rR]?|b[rR]?|B[rR]?)('''(?:.|\n)*?''')",
             (Text, String.Doc)),
            (r'[^\S\n]+', Text),
            (r'#.*$', Comment.Single),
            (r'[]{}:(),;[]', Punctuation),
            (r'\\\n', Text),
            (r'\\', Text),
            (r'(in|is|and|or|not)\b', Operator.Word),
            (r'!=|==|<<|>>|[-~+/*%=<>&^|]', Operator),
            (r'(from|import|as)\b', Keyword.Namespace),
            (r'(def|class)(\s+)', (Keyword.Declaration, Text), 'classname'),
            (r'(assert|break|continue|del|elif|else|except|exec|'
             r'finally|for|global|if|lambda|pass|print|raise|'
             r'return|try|while|yield|with)\b', Keyword),
            (r'(True|False|None)\b', Keyword.Constant),
            (r'(?i)(0x[0-9a-f]+|0o[0-7]+|0b[01]+|[0-9]+)', Number.Integer),
            (r'(?i)(\d*\.\d+|\d+\.\d*)(e[+-]?\d+)?', Number.Float),
            (r'"(\\\\|\\"|[^"])*"', String.Double),
            (r"'(\\\\|\\'|[^'])*'", String.Single),
            (r'[a-zA-Z_]\w*', Name),
        ],
        'classname': [
            (r'[a-zA-Z_]\w*', Name.Class, '#pop'),
        ],
    }