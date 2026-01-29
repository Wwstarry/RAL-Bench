from datetime import timedelta

class Duration:
    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
        # Only days, hours, minutes, seconds, microseconds are supported for arithmetic
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.microseconds = microseconds
        self._td = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)

    def total_seconds(self):
        return self._td.total_seconds()

    def __repr__(self):
        return f"<Duration {self.days}d {self.hours}h {self.minutes}m {self.seconds}s {self.microseconds}us>"

    def diff_for_humans(self, dt1, dt2, absolute=False):
        seconds = int(self.total_seconds())
        abs_seconds = abs(seconds)
        if abs_seconds < 60:
            unit = "second"
            value = abs_seconds
        elif abs_seconds < 3600:
            unit = "minute"
            value = abs_seconds // 60
        elif abs_seconds < 86400:
            unit = "hour"
            value = abs_seconds // 3600
        else:
            unit = "day"
            value = abs_seconds // 86400

        if value == 1:
            unit_str = unit
        else:
            unit_str = unit + "s"

        if absolute:
            return f"{value} {unit_str}"
        if seconds > 0:
            return f"{value} {unit_str} after"
        else:
            return f"{value} {unit_str} before"

def duration(years=0, months=0, days=0, hours=0, minutes=0, seconds=0, microseconds=0):
    return Duration(years, months, days, hours, minutes, seconds, microseconds)