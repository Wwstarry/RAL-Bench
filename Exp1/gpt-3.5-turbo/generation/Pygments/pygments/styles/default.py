from pygments.token import Token

class DefaultStyle:
    styles = {
        Token:                '',
        Token.Error:          'border: 1px solid #FF0000',
        Token.Comment:        'italic #008000',
        Token.Keyword:        'bold #0000FF',
        Token.Name:           '#000000',
        Token.Name.Function:  'bold #0000FF',
        Token.String:         '#BA2121',
        Token.Number:         '#666666',
        Token.Operator:       '#AA22FF',
        Token.Punctuation:    '#000000',
    }