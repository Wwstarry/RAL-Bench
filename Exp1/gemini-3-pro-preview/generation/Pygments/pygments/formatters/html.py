from pygments.token import Token, STANDARD_TYPES

class HtmlFormatter(object):
    name = 'HTML'
    aliases = ['html']
    filenames = ['*.html', '*.htm']

    def __init__(self, **options):
        self.options = options
        self.nowrap = options.get('nowrap', False)
        self.full = options.get('full', False)
        self.title = options.get('title', '')
        self.encoding = options.get('encoding', None)
        self.cssclass = options.get('cssclass', 'highlight')
        self.noclasses = options.get('noclasses', False)
        
        # Simple style map for noclasses=True (inline styles)
        self.style_map = {
            Token.Keyword: 'font-weight: bold; color: #008000',
            Token.Name.Class: 'font-weight: bold; color: #0000FF',
            Token.String: 'color: #BA2121',
            Token.Comment: 'color: #408080; font-style: italic',
            Token.Number: 'color: #008000',
            Token.Error: 'border: 1px solid #FF0000'
        }

    def get_style_defs(self, arg=None):
        # Minimal CSS generation
        return """
.%s .k { font-weight: bold; color: #008000 }
.%s .s { color: #BA2121 }
.%s .c { color: #408080; font-style: italic }
.%s .err { border: 1px solid #FF0000 }
""" % (self.cssclass, self.cssclass, self.cssclass, self.cssclass)

    def format(self, tokensource, outfile):
        # If outfile is None, we return a string, else we write to it
        return_string = False
        if outfile is None:
            import io
            outfile = io.StringIO()
            return_string = True

        if self.full:
            outfile.write('<!DOCTYPE html>\n<html>\n<head>\n')
            if self.title:
                outfile.write('<title>%s</title>\n' % self.title)
            outfile.write('<style type="text/css">\n')
            outfile.write(self.get_style_defs())
            outfile.write('</style>\n</head>\n<body>\n')

        if not self.nowrap:
            outfile.write('<div class="%s"><pre>' % self.cssclass)

        for ttype, value in tokensource:
            value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            style = ''
            cls = ''
            
            if self.noclasses:
                # Find best match in style_map
                tmp_type = ttype
                while tmp_type.parent:
                    if tmp_type in self.style_map:
                        style = self.style_map[tmp_type]
                        break
                    tmp_type = tmp_type.parent
            else:
                # Use standard short names
                # Simplified lookup
                if ttype in STANDARD_TYPES:
                    cls = STANDARD_TYPES[ttype]
                else:
                    # Fallback to parent
                    tmp_type = ttype
                    while tmp_type.parent:
                        if tmp_type in STANDARD_TYPES:
                            cls = STANDARD_TYPES[tmp_type]
                            break
                        tmp_type = tmp_type.parent

            if style:
                outfile.write('<span style="%s">%s</span>' % (style, value))
            elif cls:
                outfile.write('<span class="%s">%s</span>' % (cls, value))
            else:
                outfile.write(value)

        if not self.nowrap:
            outfile.write('</pre></div>\n')

        if self.full:
            outfile.write('</body>\n</html>\n')

        if return_string:
            return outfile.getvalue()