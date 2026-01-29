from datetime import datetime

def phase(date=None):
    """Calculate the lunar phase for a given date."""
    if date is None:
        date = datetime.now().date()

    # Reference new moon date: January 6, 2000
    known_new_moon = datetime(2000, 1, 6).date()
    days_since_new_moon = (date - known_new_moon).days

    # Synodic month (new moon to new moon) is approximately 29.53058867 days
    synodic_month = 29.53058867
    phase = (days_since_new_moon % synodic_month) / synodic_month

    # Convert phase to a value between 0 and 29.53
    return phase * synodic_month