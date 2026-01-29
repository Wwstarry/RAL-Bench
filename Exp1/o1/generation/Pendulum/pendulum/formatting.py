import datetime as _datetime
from .utils import local_now

def diff_for_humans(dt, other=None):
    if other is None:
        other = local_now()

    diff = dt - other
    seconds = diff.total_seconds()
    tense = "from now" if seconds > 0 else "ago"
    seconds = abs(seconds)

    if seconds < 60:
        count = int(seconds)
        unit = "second" if count == 1 else "seconds"
        return f"{count} {unit} {tense}"
    elif seconds < 3600:
        count = int(seconds // 60)
        unit = "minute" if count == 1 else "minutes"
        return f"{count} {unit} {tense}"
    elif seconds < 86400:
        count = int(seconds // 3600)
        unit = "hour" if count == 1 else "hours"
        return f"{count} {unit} {tense}"
    else:
        count = int(seconds // 86400)
        unit = "day" if count == 1 else "days"
        return f"{count} {unit} {tense}"