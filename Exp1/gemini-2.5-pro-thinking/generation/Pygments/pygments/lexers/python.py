"""
    pygments.lexers.python
    ~~~~~~~~~~~~~~~~~~~~~~

    Lexers for Python and related languages.

    :copyright: Copyright 2006-2021 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from pygments.lexer import RegexLexer, bygroups
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation

__all__ = ['PythonLexer']


class PythonLexer(RegexLexer):
    """
    For Python source code.
    """
    name = 'Python'
    aliases = ['python', 'py']
    filenames = ['*.py', '*.pyw', '*.pyi']
    mimetypes = ['text/x-python', 'application/x-python']

    flags = re.MULTILINE | re.UNICODE

    def innerstring_rules(ttype):
        return [
            # the old style '%s' % (...) string formatting
            (r'%(\(\w+\))?[-#0 +]*([0-9]+|[*])?(\.([0-9]+|[*]))?'
             '[hlL]?[diouxXeEfFgGcrs%]', String.Interpol),
            # the new style '{...}' string formatting
            (r'\{'
             r'((\w+)((\.\w+)|(\[[^\]]+\]))*)?'  # field name
             r'(\
![sra])
?'                       # conversion
             r'(\:(.?[<>=\^])?[-+ ]?#?0?(\d+)?,?(\.\d+)?[bcdeEfFgGnosxX%]?)?'
             r'\}', String.Interpol),
            (r'[^\\\'"%{\n]+', ttype),
            (r'[\'"\\]', ttype),
            (r'%', ttype),
            (r'\{', ttype),
        ]

    tokens = {
        'root': [
            (r'\n', Text),
            (r'^(\s*)([rRuU]{,2})("""(?:.|\n)*?""")',
             bygroups(Text, String.Affix, String.Doc)),
            (r"^(\s*)([rRuU]{,2})('''(?:.|\n)*?''')",
             bygroups(Text, String.Affix, String.Doc)),
            (r'[^\S\n]+', Text),
            (r'#.*$', Comment.Single),
            (r'[]{}:(),;[]', Punctuation),
            (r'\\\n', Text),
            (r'\\', Text),
            (r'(in|is|and|or|not)\b', Operator.Word),
            (r'!=|==|<<|>>|[-~+/*%=<>&^|.]', Operator),
            (r'(from|import|as|while|for|break|continue|if|elif|else|try|'
             r'except|finally|with|return|yield|raise|assert|pass|del|'
             r'global|nonlocal|lambda|def|class|async|await)\b', Keyword),
            (r'(True|False|None)\b', Keyword.Constant),
            (r'__\w+__\b', Name.Builtin.Pseudo),
            (r'(self|cls)\b', Name.Builtin.Pseudo),
            (r'(@)(\s*)(\w+)', bygroups(Name.Decorator, Text, Name.Decorator)),
            (r'(?<!\.)(Exception|TypeError|ValueError|NameError|AttributeError|'
             r'SyntaxError|IndentationError|KeyError|IndexError|IOError|'
             r'ZeroDivisionError|ImportError|RuntimeError|StopIteration|'
             r'SystemExit|KeyboardInterrupt)\b', Name.Exception),
            (r'(?<!\.)(abs|all|any|bin|bool|bytearray|bytes|callable|chr|'
             r'classmethod|compile|complex|delattr|dict|dir|divmod|enumerate|'
             r'eval|exec|filter|float|format|frozenset|getattr|globals|hasattr|'
             r'hash|help|hex|id|input|int|isinstance|issubclass|iter|len|'
             r'list|locals|map|max|memoryview|min|next|object|oct|open|ord|'
             r'pow|print|property|range|repr|reversed|round|set|setattr|slice|'
             r'sorted|staticmethod|str|sum|super|tuple|type|vars|zip)\b',
             Name.Builtin),
            (r'[rR][fF]?\'', String.Affix, 'rsingle'),
            (r'[rR][fF]?"', String.Affix, 'rdouble'),
            (r'[fF][rR]?\'', String.Affix, 'rsingle'),
            (r'[fF][rR]?"', String.Affix, 'rdouble'),
            (r'[uU]\'', String.Affix, 'usingle'),
            (r'[uU]"', String.Affix, 'udouble'),
            (r'[rR]\'', String.Affix, 'rsingle'),
            (r'[rR]"', String.Affix, 'rdouble'),
            (r'\'', String.Single, 'single'),
            (r'"', String.Double, 'double'),
            (r'[a-zA-Z_]\w*', Name),
            (r'0[oO][0-7]+', Number.Oct),
            (r'0[bB][01]+', Number.Bin),
            (r'0[xX][a-fA-F0-9]+', Number.Hex),
            (r'(\d+\.\d*|\.\d+)([eE][-+]?\d+)?', Number.Float),
            (r'\d+[eE][-+]?\d+', Number.Float),
            (r'\d+', Number.Integer),
        ],
        'single': [
            (r'\\.', String.Escape),
            (r'\'', String.Single, '#pop'),
            (r'[^\'\\]+', String.Single),
        ],
        'double': [
            (r'\\.', String.Escape),
            (r'"', String.Double, '#pop'),
            (r'[^"\\]+', String.Double),
        ],
        'rsingle': innerstring_rules(String.Single) + [
            (r'\'', String.Affix, '#pop'),
        ],
        'rdouble': innerstring_rules(String.Double) + [
            (r'"', String.Affix, '#pop'),
        ],
        'usingle': [
            (r'\\.', String.Escape),
            (r'\'', String.Affix, '#pop'),
            (r'[^\\\'\n]+', String.Single),
            (r'\n', String.Single),
        ],
        'udouble': [
            (r'\\.', String.Escape),
            (r'"', String.Affix, '#pop'),
            (r'[^\\"\n]+', String.Double),
            (r'\n', String.Double),
        ],
    }