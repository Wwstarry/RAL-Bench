import datetime as _datetime

def local_now():
    return _datetime.datetime.now(_datetime.timezone.utc).astimezone()

def parse_iso8601(dt_str):
    try:
        dt = _datetime.datetime.fromisoformat(dt_str)
        return dt
    except ValueError:
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S.%f%z",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ]
        for f in formats:
            try:
                dt = _datetime.datetime.strptime(dt_str, f)
                return dt
            except ValueError:
                pass
        raise ValueError(f"Unable to parse ISO 8601 datetime: {dt_str}")