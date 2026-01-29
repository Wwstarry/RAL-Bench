class Query:
    def __init__(self, field):
        self._field = field

    def equals(self, value):
        return lambda record: record.get(self._field) == value

    def not_equals(self, value):
        return lambda record: record.get(self._field) != value

    def greater_than(self, value):
        return lambda record: record.get(self._field, 0) > value

    def less_than(self, value):
        return lambda record: record.get(self._field, 0) < value

    def match(self, record):
        raise NotImplementedError("Use specific query methods like equals, not_equals, etc.")