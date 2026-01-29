# -*- coding: utf-8 -*-

class Formatter:
    """
    Handles formatting of durations for human-readable output.
    """
    def __init__(self, locale="en"):
        if locale != "en":
            # For simplicity, we only support English
            pass
        self._locale = locale

    def format_diff(self, duration, absolute=False, is_now=False):
        """
        Formats a Duration object into a human-readable string.
        """
        if is_now:
            return "now"

        total_seconds = duration.total_seconds()
        
        if total_seconds == 0 and duration.years == 0 and duration.months == 0:
            return "now"

        is_future = total_seconds < 0
        
        # Pendulum's diff logic is complex, involving month/year boundaries.
        # This is a simplified version based on total seconds for broader compatibility.
        s = abs(total_seconds)
        
        # Approximations for month and year
        days = abs(duration.in_days())
        months = abs(duration.in_months())
        years = abs(duration.in_years())

        if s < 1:
            return "now"
        
        unit, count = None, 0
        
        if years >= 1:
            unit, count = "year", round(years)
        elif months >= 1:
            unit, count = "month", round(months)
        elif days >= 7:
            unit, count = "week", round(days / 7)
        elif days >= 1:
            unit, count = "day", round(days)
        elif s >= 3600:
            unit, count = "hour", round(s / 3600)
        elif s >= 60:
            unit, count = "minute", round(s / 60)
        else:
            unit, count = "second", round(s)

        if count == 0:
            count = 1

        if count > 1:
            unit += "s"

        if absolute:
            return f"{count} {unit}"

        if is_future:
            return f"in {count} {unit}"
        
        return f"{count} {unit} ago"