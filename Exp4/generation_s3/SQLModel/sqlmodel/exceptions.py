class SQLModelError(Exception):
    pass


class TableNotCreatedError(SQLModelError):
    pass


class UnmappedInstanceError(SQLModelError, TypeError):
    pass


class MultiplePrimaryKeyError(SQLModelError, ValueError):
    pass