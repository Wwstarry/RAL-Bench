def diff_for_humans(dt1, dt2=None, absolute=False):
    if dt2 is None:
        dt2 = DateTime.utcnow()
    
    diff = dt1 - dt2 if dt1 > dt2 else dt2 - dt1
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)} seconds ago" if not absolute else f"{int(seconds)} seconds"
    minutes = seconds / 60
    if minutes < 60:
        return f"{int(minutes)} minutes ago" if not absolute else f"{int(minutes)} minutes"
    hours = minutes / 60
    if hours < 24:
        return f"{int(hours)} hours ago" if not absolute else f"{int(hours)} hours"
    days = hours / 24
    if days < 30:
        return f"{int(days)} days ago" if not absolute else f"{int(days)} days"
    months = days / 30
    if months < 12:
        return f"{int(months)} months ago" if not absolute else f"{int(months)} months"
    years = days / 365
    return f"{int(years)} years ago" if not absolute else f"{int(years)} years"