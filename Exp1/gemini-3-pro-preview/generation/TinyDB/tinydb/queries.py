class Query:
    """
    Provides a way to construct queries.
    Usage: Query().field == value
    """
    def __getattr__(self, item):
        return QueryInstance(item)

class QueryInstance:
    """
    Represents a condition on a specific field.
    """
    def __init__(self, field):
        self._field = field
        self._test = lambda x: False

    def __call__(self, doc):
        """
        Evaluate the query against a document.
        """
        return self._test(doc.get(self._field))

    def __eq__(self, other):
        self._test = lambda val: val == other
        return self

    def __ne__(self, other):
        self._test = lambda val: val != other
        return self

    def __lt__(self, other):
        self._test = lambda val: val is not None and val < other
        return self

    def __gt__(self, other):
        self._test = lambda val: val is not None and val > other
        return self

    def __le__(self, other):
        self._test = lambda val: val is not None and val <= other
        return self

    def __ge__(self, other):
        self._test = lambda val: val is not None and val >= other
        return self

    def test(self, func):
        """
        Custom test function.
        Usage: Query().field.test(lambda x: x > 0)
        """
        self._test = func
        return self

    def exists(self):
        """Checks if the field exists in the document."""
        def _exists_check(doc):
            return self._field in doc
        
        # We override __call__ here because we need the whole doc, not just the value
        self.__call__ = _exists_check
        return self

# Alias for readability
where = Query()