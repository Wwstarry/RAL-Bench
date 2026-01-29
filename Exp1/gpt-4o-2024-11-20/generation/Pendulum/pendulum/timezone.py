from datetime import timezone as dt_timezone, timedelta

class Timezone:
    def __init__(self, name):
        self.name = name
        self.offset = self._get_offset(name)

    def _get_offset(self, name):
        if name == "UTC":
            return timedelta(0)
        raise ValueError(f"Unsupported timezone: {name}")

    def to_datetime_timezone(self):
        return dt_timezone(self.offset)

def timezone(name):
    return Timezone(name).to_datetime_timezone()