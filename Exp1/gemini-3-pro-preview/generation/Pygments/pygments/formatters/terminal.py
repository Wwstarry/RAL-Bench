from pygments.token import Token

class TerminalFormatter(object):
    name = 'Terminal'
    aliases = ['terminal', 'console']
    filenames = []

    def __init__(self, **options):
        self.options = options
        self.encoding = options.get('encoding', None)
        
        # ANSI Color Map
        self.colors = {
            Token.Keyword: '\x1b[32;01m', # Green Bold
            Token.Name.Class: '\x1b[34;01m', # Blue Bold
            Token.String: '\x1b[31m', # Red
            Token.Comment: '\x1b[36m', # Cyan
            Token.Number: '\x1b[32m', # Green
            Token.Error: '\x1b[31;01m', # Red Bold
        }
        self.reset = '\x1b[39;49;00m'

    def format(self, tokensource, outfile):
        return_string = False
        if outfile is None:
            import io
            outfile = io.StringIO()
            return_string = True

        for ttype, value in tokensource:
            color = ''
            tmp_type = ttype
            while tmp_type.parent:
                if tmp_type in self.colors:
                    color = self.colors[tmp_type]
                    break
                tmp_type = tmp_type.parent
            
            if color:
                outfile.write(color + value + self.reset)
            else:
                outfile.write(value)

        if return_string:
            return outfile.getvalue()