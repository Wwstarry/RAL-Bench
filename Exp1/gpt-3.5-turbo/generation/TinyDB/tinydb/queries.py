class Query:
    def __init__(self, field=None):
        self.field = field

    def __call__(self, document):
        if self.field is None:
            return True
        return document.get(self.field)

    def __eq__(self, other):
        return lambda doc: doc.get(self.field) == other

    def __ne__(self, other):
        return lambda doc: doc.get(self.field) != other

    def __lt__(self, other):
        return lambda doc: doc.get(self.field) < other

    def __le__(self, other):
        return lambda doc: doc.get(self.field) <= other

    def __gt__(self, other):
        return lambda doc: doc.get(self.field) > other

    def __ge__(self, other):
        return lambda doc: doc.get(self.field) >= other

    def exists(self):
        return lambda doc: self.field in doc

    def matches(self, func):
        """
        Accept a function that takes the field value and returns bool.
        """
        return lambda doc: func(doc.get(self.field))

    def __and__(self, other):
        return lambda doc: self(doc) and other(doc)

    def __or__(self, other):
        return lambda doc: self(doc) or other(doc)

    def __invert__(self):
        return lambda doc: not self(doc)


# Provide a shortcut to create Query objects for fields
def q(field):
    return Query(field)


# For convenience, expose Query as Query
Query = Query