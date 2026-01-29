import re

class QueryImpl:
    """
    A query implementation.
    
    It is not meant to be used directly. Use ``Query`` instead.
    """
    def __init__(self, test, path):
        self.test = test
        self.path = path

    def __call__(self, doc):
        # Resolve path
        try:
            value = doc
            for key in self.path:
                value = value[key]
        except (KeyError, TypeError):
            return False # Path doesn't exist

        return self.test(value)

    # --- Logical operators ---
    def __and__(self, other):
        return AndQuery([self, other])

    def __or__(self, other):
        return OrQuery([self, other])

    def __invert__(self):
        return NotQuery(self)

class AndQuery(QueryImpl):
    def __init__(self, queries):
        super().__init__(None, None)
        self.queries = queries

    def __call__(self, doc):
        return all(q(doc) for q in self.queries)
    
    def __and__(self, other):
        self.queries.append(other)
        return self

class OrQuery(QueryImpl):
    def __init__(self, queries):
        super().__init__(None, None)
        self.queries = queries

    def __call__(self, doc):
        return any(q(doc) for q in self.queries)

    def __or__(self, other):
        self.queries.append(other)
        return self

class NotQuery(QueryImpl):
    def __init__(self, query):
        super().__init__(None, None)
        self.query = query

    def __call__(self, doc):
        return not self.query(doc)

class QueryBuilder:
    def __init__(self, path=None):
        self._path = path or []

    def __getattr__(self, item):
        return QueryBuilder(self._path + [item])

    def __getitem__(self, item):
        return QueryBuilder(self._path + [item])

    def _generate_query(self, test):
        return QueryImpl(test, self._path)

    # --- Comparison operators ---
    def __eq__(self, rhs):
        return self._generate_query(lambda val: val == rhs)

    def __ne__(self, rhs):
        return self._generate_query(lambda val: val != rhs)

    def __lt__(self, rhs):
        return self._generate_query(lambda val: val < rhs)

    def __le__(self, rhs):
        return self._generate_query(lambda val: val <= rhs)

    def __gt__(self, rhs):
        return self._generate_query(lambda val: val > rhs)

    def __ge__(self, rhs):
        return self._generate_query(lambda val: val >= rhs)

    # --- Other tests ---
    def exists(self):
        def test(doc):
            try:
                val = doc
                for key in self._path:
                    val = val[key]
                return True
            except (KeyError, TypeError):
                return False
        # This is a special query that doesn't use the standard __call__
        q = QueryImpl(None, None)
        q.__call__ = test
        return q

    def matches(self, regex, flags=0):
        return self._generate_query(
            lambda val: isinstance(val, str) and re.match(regex, val, flags) is not None
        )

    def test(self, func, *args):
        return self._generate_query(lambda val: func(val, *args))

    def any(self, cond):
        if isinstance(cond, (list, tuple)):
            # e.g. where('field').any(['val1', 'val2'])
            return self._generate_query(lambda val: any(item in val for item in cond))
        else:
            # e.g. where('field').any(where('subfield') == 1)
            return self._generate_query(lambda val: any(cond(item) for item in val))

    def all(self, cond):
        if isinstance(cond, (list, tuple)):
            # e.g. where('field').all(['val1', 'val2'])
            return self._generate_query(lambda val: all(item in val for item in cond))
        else:
            # e.g. where('field').all(where('subfield') == 1)
            return self._generate_query(lambda val: all(cond(item) for item in val))


Query = QueryBuilder()
where = Query