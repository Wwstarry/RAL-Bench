class Query:
    """
    A simple query class that can be used to match documents.
    Example usage:
        from tinydb.queries import where
        table.search(where('status').equals('open'))
    """

    def __init__(self, field):
        self.field = field
        self._test_func = None

    def equals(self, value):
        def test(doc):
            return doc.get(self.field) == value
        self._test_func = test
        return self

    def test(self, doc):
        if self._test_func:
            return self._test_func(doc)
        return False

def where(field):
    return Query(field)