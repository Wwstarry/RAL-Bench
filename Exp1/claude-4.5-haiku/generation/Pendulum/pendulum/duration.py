import datetime as _datetime

class Duration(_datetime.timedelta):
    """A Duration class extending timedelta with additional methods."""
    
    def __new__(cls, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0):
        total_seconds = (
            days * 86400 +
            seconds +
            microseconds / 1000000 +
            milliseconds / 1000 +
            minutes * 60 +
            hours * 3600 +
            weeks * 604800
        )
        
        instance = _datetime.timedelta.__new__(
            cls,
            days=0,
            seconds=total_seconds,
            microseconds=0
        )
        return instance
    
    def as_timedelta(self):
        """Convert to a standard timedelta."""
        return _datetime.timedelta(seconds=self.total_seconds())
    
    def in_words(self, locale='en'):
        """Get a human-readable representation."""
        total_seconds = self.total_seconds()
        
        if total_seconds < 0:
            sign = "-"
            total_seconds = abs(total_seconds)
        else:
            sign = ""
        
        days = int(total_seconds // 86400)
        remaining = total_seconds % 86400
        hours = int(remaining // 3600)
        remaining = remaining % 3600
        minutes = int(remaining // 60)
        seconds = int(remaining % 60)
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        if not parts:
            return "0 seconds"
        
        return sign + ", ".join(parts)
    
    def __repr__(self):
        return f"Duration(seconds={self.total_seconds()})"
    
    def __str__(self):
        return self.in_words()