# Token definitions

class _TokenType(tuple):
    def __new__(cls, name, parent=None):
        obj = tuple.__new__(cls, (name,))
        obj.parent = parent
        obj.name = name
        return obj

    def __getattr__(self, attr):
        return getattr(self.parent, attr)

    def __repr__(self):
        return 'Token.' + self.name

    def __call__(self, value):
        return (self, value)

class _TokenMeta(type):
    def __getattr__(self, name):
        t = _TokenType(name, self)
        setattr(self, name, t)
        return t

class Token(metaclass=_TokenMeta):
    Text = _TokenType('Text')
    Whitespace = _TokenType('Whitespace', Text)
    Error = _TokenType('Error')
    Other = _TokenType('Other')
    Keyword = _TokenType('Keyword')
    Keyword_Constant = _TokenType('Keyword.Constant', Keyword)
    Keyword_Declaration = _TokenType('Keyword.Declaration', Keyword)
    Keyword_Namespace = _TokenType('Keyword.Namespace', Keyword)
    Keyword_Pseudo = _TokenType('Keyword.Pseudo', Keyword)
    Keyword_Reserved = _TokenType('Keyword.Reserved', Keyword)
    Keyword_Type = _TokenType('Keyword.Type', Keyword)
    Name = _TokenType('Name')
    Name_Builtin = _TokenType('Name.Builtin', Name)
    Name_Function = _TokenType('Name.Function', Name)
    Name_Class = _TokenType('Name.Class', Name)
    Name_Namespace = _TokenType('Name.Namespace', Name)
    Name_Exception = _TokenType('Name.Exception', Name)
    Name_Variable = _TokenType('Name.Variable', Name)
    Name_Constant = _TokenType('Name.Constant', Name)
    Name_Label = _TokenType('Name.Label', Name)
    Name_Entity = _TokenType('Name.Entity', Name)
    Name_Attribute = _TokenType('Name.Attribute', Name)
    Name_Tag = _TokenType('Name.Tag', Name)
    Name_Decorator = _TokenType('Name.Decorator', Name)
    Literal = _TokenType('Literal')
    Literal_String = _TokenType('Literal.String', Literal)
    Literal_String_Double = _TokenType('Literal.String.Double', Literal_String)
    Literal_String_Single = _TokenType('Literal.String.Single', Literal_String)
    Literal_String_Interpol = _TokenType('Literal.String.Interpol', Literal_String)
    Literal_String_Regex = _TokenType('Literal.String.Regex', Literal_String)
    Literal_String_Symbol = _TokenType('Literal.String.Symbol', Literal_String)
    Literal_String_Other = _TokenType('Literal.String.Other', Literal_String)
    Literal_Number = _TokenType('Literal.Number', Literal)
    Literal_Number_Integer = _TokenType('Literal.Number.Integer', Literal_Number)
    Literal_Number_Float = _TokenType('Literal.Number.Float', Literal_Number)
    Literal_Number_Hex = _TokenType('Literal.Number.Hex', Literal_Number)
    Literal_Number_Oct = _TokenType('Literal.Number.Oct', Literal_Number)
    Operator = _TokenType('Operator')
    Operator_Word = _TokenType('Operator.Word', Operator)
    Punctuation = _TokenType('Punctuation')
    Comment = _TokenType('Comment')
    Comment_Multiline = _TokenType('Comment.Multiline', Comment)
    Comment_Preproc = _TokenType('Comment.Preproc', Comment)
    Comment_Single = _TokenType('Comment.Single', Comment)
    Comment_Special = _TokenType('Comment.Special', Comment)
    Generic = _TokenType('Generic')
    Generic_Deleted = _TokenType('Generic.Deleted', Generic)
    Generic_Emph = _TokenType('Generic.Emph', Generic)
    Generic_Error = _TokenType('Generic.Error', Generic)
    Generic_Heading = _TokenType('Generic.Heading', Generic)
    Generic_Insert = _TokenType('Generic.Insert', Generic)
    Generic_Output = _TokenType('Generic.Output', Generic)
    Generic_Prompt = _TokenType('Generic.Prompt', Generic)
    Generic_Strong = _TokenType('Generic.Strong', Generic)
    Generic_Subheading = _TokenType('Generic.Subheading', Generic)
    Generic_Traceback = _TokenType('Generic.Traceback', Generic)

# For compatibility
STANDARD_TYPES = {
    'Text': Token.Text,
    'Whitespace': Token.Whitespace,
    'Error': Token.Error,
    'Other': Token.Other,
    'Keyword': Token.Keyword,
    'Keyword.Constant': Token.Keyword_Constant,
    'Keyword.Declaration': Token.Keyword_Declaration,
    'Keyword.Namespace': Token.Keyword_Namespace,
    'Keyword.Pseudo': Token.Keyword_Pseudo,
    'Keyword.Reserved': Token.Keyword_Reserved,
    'Keyword.Type': Token.Keyword_Type,
    'Name': Token.Name,
    'Name.Builtin': Token.Name_Builtin,
    'Name.Function': Token.Name_Function,
    'Name.Class': Token.Name_Class,
    'Name.Namespace': Token.Name_Namespace,
    'Name.Exception': Token.Name_Exception,
    'Name.Variable': Token.Name_Variable,
    'Name.Constant': Token.Name_Constant,
    'Name.Label': Token.Name_Label,
    'Name.Entity': Token.Name_Entity,
    'Name.Attribute': Token.Name_Attribute,
    'Name.Tag': Token.Name_Tag,
    'Name.Decorator': Token.Name_Decorator,
    'Literal': Token.Literal,
    'Literal.String': Token.Literal_String,
    'Literal.String.Double': Token.Literal_String_Double,
    'Literal.String.Single': Token.Literal_String_Single,
    'Literal.String.Interpol': Token.Literal_String_Interpol,
    'Literal.String.Regex': Token.Literal_String_Regex,
    'Literal.String.Symbol': Token.Literal_String_Symbol,
    'Literal.String.Other': Token.Literal_String_Other,
    'Literal.Number': Token.Literal_Number,
    'Literal.Number.Integer': Token.Literal_Number_Integer,
    'Literal.Number.Float': Token.Literal_Number_Float,
    'Literal.Number.Hex': Token.Literal_Number_Hex,
    'Literal.Number.Oct': Token.Literal_Number_Oct,
    'Operator': Token.Operator,
    'Operator.Word': Token.Operator_Word,
    'Punctuation': Token.Punctuation,
    'Comment': Token.Comment,
    'Comment.Multiline': Token.Comment_Multiline,
    'Comment.Preproc': Token.Comment_Preproc,
    'Comment.Single': Token.Comment_Single,
    'Comment.Special': Token.Comment_Special,
    'Generic': Token.Generic,
    'Generic.Deleted': Token.Generic_Deleted,
    'Generic.Emph': Token.Generic_Emph,
    'Generic.Error': Token.Generic_Error,
    'Generic.Heading': Token.Generic_Heading,
    'Generic.Insert': Token.Generic_Insert,
    'Generic.Output': Token.Generic_Output,
    'Generic.Prompt': Token.Generic_Prompt,
    'Generic.Strong': Token.Generic_Strong,
    'Generic.Subheading': Token.Generic_Subheading,
    'Generic.Traceback': Token.Generic_Traceback,
}