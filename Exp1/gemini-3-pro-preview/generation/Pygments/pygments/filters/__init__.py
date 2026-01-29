# Filters allow post-processing of the token stream.
# Minimal implementation for structure compatibility.

class Filter(object):
    def __init__(self, **options):
        self.options = options

    def filter(self, lexer, stream):
        raise NotImplementedError()