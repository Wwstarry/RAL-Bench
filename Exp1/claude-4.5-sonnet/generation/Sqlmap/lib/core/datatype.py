"""
Custom data types
"""


class AttribDict(dict):
    """
    Dictionary with attribute-style access
    """
    def __init__(self, *args, **kwargs):
        super(AttribDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError("'AttribDict' object has no attribute '%s'" % name)
    
    def __setattr__(self, name, value):
        self[name] = value