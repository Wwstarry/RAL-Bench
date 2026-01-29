from pygments.token import Keyword, Name, Comment, String, Error, \
     Number, Operator, Generic

class DefaultStyle(object):
    # Minimal style object
    background_color = "#f8f8f8"
    highlight_color = "#ffffcc"
    
    styles = {
        Keyword: 'bold #008000',
        Name.Class: 'bold #0000FF',
        String: '#BA2121',
        Comment: 'italic #408080',
        Number: '#008000',
        Error: 'border:#FF0000',
    }