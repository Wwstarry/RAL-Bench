from functools import reduce

class BaseQuery:
    """
    The base class for all queries.
    Queries are callable objects that return ``True`` or ``False``
    for a given document.
    They can be combined using the logical operators ``&``, ``|``, and ``~``.
    """
    def __call__(self, doc):
        raise NotImplementedError

    def __and__(self, other):
        return And(self, other)

    def __or__(self, other):
        return Or(self, other)

    def __invert__(self):
        return Not(self)

class And(BaseQuery):
    """
    A query that is true if both subqueries are true.
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, doc):
        return self.left(doc) and self.right(doc)

class Or(BaseQuery):
    """
    A query that is true if either subquery is true.
    """
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __call__(self, doc):
        return self.left(doc) or self.right(doc)

class Not(BaseQuery):
    """
    A query that is true if the subquery is false.
    """
    def __init__(self, query):
        self.query = query

    def __call__(self, doc):
        return not self.query(doc)

class QueryImpl(BaseQuery):
    """
    The implementation of a query.
    It is created by the ``QueryBuilder`` and evaluates a test on a document.
    """
    def __init__(self, path, test):
        self.path = path
        self.test = test

    def __call__(self, doc):
        try:
            value = reduce(lambda d, key: d.get(key) if isinstance(d, dict) else None, self.path, doc)
            return self.test(value)
        except TypeError:
            return False

class QueryBuilder:
    """
    A query builder that allows creating queries in a more intuitive way.

    Example:
        >>> Query = QueryBuilder()
        >>> query = (Query.name == 'John') & (Query.age > 18)
    """
    def __init__(self, path=None):
        self._path = path or []

    def __getattr__(self, item):
        return QueryBuilder(self._path + [item])

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __eq__(self, rhs):
        return QueryImpl(self._path, lambda val: val == rhs)

    def __ne__(self, rhs):
        return QueryImpl(self._path, lambda val: val != rhs)

    def __lt__(self, rhs):
        return QueryImpl(self._path, lambda val: val is not None and val < rhs)

    def __le__(self, rhs):
        return QueryImpl(self._path, lambda val: val is not None and val <= rhs)

    def __gt__(self, rhs):
        return QueryImpl(self._path, lambda val: val is not None and val > rhs)

    def __ge__(self, rhs):
        return QueryImpl(self._path, lambda val: val is not None and val >= rhs)

    def exists(self):
        """
        Check if a key exists in a document.
        """
        class ExistsQuery(BaseQuery):
            def __init__(self, path):
                self.path = path
            def __call__(self, doc):
                try:
                    reduce(lambda d, key: d[key], self.path, doc)
                    return True
                except (KeyError, TypeError):
                    return False
        return ExistsQuery(self._path)

    def test(self, func, *args):
        """
        Run a custom test function on a field.

        :param func: The function to run. It will receive the field's value
                     and the arguments passed to this method.
        """
        return QueryImpl(self._path, lambda val: func(val, *args))

# The user will interact with an instance of this class
Query = QueryBuilder()