class Query:
    def __init__(self, field=None):
        self.field = field

    def __getattr__(self, name):
        return Query(name)

    def __eq__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value == value
        return condition

    def __ne__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value != value
        return condition

    def __lt__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value is not None and field_value < value
        return condition

    def __le__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value is not None and field_value <= value
        return condition

    def __gt__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value is not None and field_value > value
        return condition

    def __ge__(self, value):
        def condition(doc):
            field_value = doc.get(self.field)
            return field_value is not None and field_value >= value
        return condition

    def __and__(self, other):
        def condition(doc):
            return self(doc) and other(doc)
        return condition

    def __or__(self, other):
        def condition(doc):
            return self(doc) or other(doc)
        return condition

    def __invert__(self):
        def condition(doc):
            return not self(doc)
        return condition

    def __call__(self, doc):
        raise NotImplementedError("Query must be used with comparison operator")

def where(field):
    return Query(field)