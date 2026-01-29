def humanize_duration(duration):
    seconds = abs(duration.total_seconds())
    if seconds < 60:
        return f"{int(seconds)} seconds ago" if duration.total_seconds() < 0 else f"in {int(seconds)} seconds"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{int(minutes)} minutes ago" if duration.total_seconds() < 0 else f"in {int(minutes)} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{int(hours)} hours ago" if duration.total_seconds() < 0 else f"in {int(hours)} hours"
    else:
        days = seconds // 86400
        return f"{int(days)} days ago" if duration.total_seconds() < 0 else f"in {int(days)} days"