from datetime import datetime, timedelta
from math import cos, sin, tan, acos, asin, radians, degrees
import pytz

def calculate_solar_declination(day_of_year: int) -> float:
    """Calculate the solar declination angle in degrees."""
    return 23.44 * sin(radians((360 / 365) * (day_of_year - 81)))

def calculate_hour_angle(latitude: float, declination: float, zenith: float) -> float:
    """Calculate the hour angle for sunrise/sunset."""
    latitude_rad = radians(latitude)
    declination_rad = radians(declination)
    zenith_rad = radians(zenith)
    cos_h = (cos(zenith_rad) - sin(latitude_rad) * sin(declination_rad)) / (cos(latitude_rad) * cos(declination_rad))
    if cos_h < -1 or cos_h > 1:
        raise ValueError("Sun never rises or sets on this date at this location.")
    return degrees(acos(cos_h))

def calculate_event(observer, date, zenith, is_rise, tzinfo):
    """Calculate the time of a solar event (sunrise or sunset)."""
    day_of_year = date.timetuple().tm_yday
    declination = calculate_solar_declination(day_of_year)
    hour_angle = calculate_hour_angle(observer.latitude, declination, zenith)
    if not is_rise:
        hour_angle = -hour_angle

    # Approximate solar noon
    solar_noon = 12.0 - (observer.longitude / 15.0)
    event_time = solar_noon + (hour_angle / 15.0)

    # Convert to UTC datetime
    utc_time = datetime(date.year, date.month, date.day, tzinfo=pytz.UTC) + timedelta(hours=event_time)
    return utc_time.astimezone(tzinfo)

def sun(observer, date=None, tzinfo=None):
    """Calculate dawn, sunrise, noon, sunset, and dusk times."""
    if date is None:
        date = datetime.now().date()
    if tzinfo is None:
        tzinfo = pytz.UTC

    zeniths = {
        "dawn": 96,
        "sunrise": 90.833,
        "noon": 90,
        "sunset": 90.833,
        "dusk": 96,
    }

    times = {}
    for event, zenith in zeniths.items():
        is_rise = event in ["dawn", "sunrise"]
        times[event] = calculate_event(observer, date, zenith, is_rise, tzinfo)

    return times

def sunrise(observer, date=None, tzinfo=None):
    """Calculate the time of sunrise."""
    return sun(observer, date, tzinfo)["sunrise"]

def sunset(observer, date=None, tzinfo=None):
    """Calculate the time of sunset."""
    return sun(observer, date, tzinfo)["sunset"]