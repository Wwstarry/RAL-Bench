"""Token types and standard type definitions."""

class _TokenType(tuple):
    def __init__(self, *args):
        super(_TokenType, self).__init__(args)
        self.parent = None
    
    def __getattr__(self, name):
        new = _TokenType(*self + (name,))
        new.parent = self
        setattr(self, name, new)
        return new
    
    def __repr__(self):
        return 'Token' + ('.' if self else '') + '.'.join(self)

# Create token hierarchy
Token = _TokenType()

# Standard token types mapping
STANDARD_TYPES = {
    Token:                         't',
    
    Token.Text:                    '',
    Token.Text.Whitespace:         'w',
    Token.Text.Punctuation:        'p',
    
    Token.Error:                   'err',
    Token.Other:                   'x',
    
    Token.Keyword:                 'k',
    Token.Keyword.Constant:        'kc',
    Token.Keyword.Declaration:     'kd',
    Token.Keyword.Namespace:       'kn',
    Token.Keyword.Reserved:        'kr',
    Token.Keyword.Type:            'kt',
    
    Token.Name:                    'n',
    Token.Name.Attribute:          'na',
    Token.Name.Builtin:            'nb',
    Token.Name.Class:              'nc',
    Token.Name.Constant:           'no',
    Token.Name.Decorator:          'nd',
    Token.Name.Entity:             'ni',
    Token.Name.Exception:          'ne',
    Token.Name.Function:           'nf',
    Token.Name.Property:           'py',
    Token.Name.Label:              'nl',
    Token.Name.Namespace:          'nn',
    Token.Name.Other:              'nx',
    Token.Name.Tag:                'nt',
    Token.Name.Variable:           'nv',
    
    Token.Literal:                 'l',
    Token.Literal.Date:            'ld',
    
    Token.Literal.String:          's',
    Token.Literal.String.Backtick: 'sb',
    Token.Literal.String.Char:     'sc',
    Token.Literal.String.Doc:      'sd',
    Token.Literal.String.Double:   's2',
    Token.Literal.String.Escape:   'se',
    Token.Literal.String.Heredoc:  'sh',
    Token.Literal.String.Interpol: 'si',
    Token.Literal.String.Other:    'sx',
    Token.Literal.String.Regex:    'sr',
    Token.Literal.String.Single:   's1',
    Token.Literal.String.Symbol:   'ss',
    
    Token.Literal.Number:          'm',
    Token.Literal.Number.Bin:      'mb',
    Token.Literal.Number.Float:    'mf',
    Token.Literal.Number.Hex:      'mh',
    Token.Literal.Number.Integer:  'mi',
    Token.Literal.Number.Oct:      'mo',
    
    Token.Operator:                'o',
    Token.Operator.Word:           'ow',
    
    Token.Punctuation:             'p',
    
    Token.Comment:                 'c',
    Token.Comment.Multiline:       'cm',
    Token.Comment.Preproc:         'cp',
    Token.Comment.Single:          'c1',
    Token.Comment.Special:         'cs',
    
    Token.Generic:                 'g',
    Token.Generic.Deleted:         'gd',
    Token.Generic.Emph:            'ge',
    Token.Generic.Error:           'gr',
    Token.Generic.Heading:         'gh',
    Token.Generic.Inserted:        'gi',
    Token.Generic.Output:          'go',
    Token.Generic.Prompt:          'gp',
    Token.Generic.Strong:          'gs',
    Token.Generic.Subheading:      'gu',
    Token.Generic.Traceback:       'gt',
}