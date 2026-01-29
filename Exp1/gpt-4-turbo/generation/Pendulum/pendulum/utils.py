def is_naive(dt):
    return dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None

from .timezone import local_timezone