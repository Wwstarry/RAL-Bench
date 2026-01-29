import datetime

class relativedelta:
    def __init__(self, years=0, months=0, days=0, hours=0, minutes=0, seconds=0):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds

    def __add__(self, other):
        if isinstance(other, datetime.datetime):
            year = other.year + self.years
            month = other.month + self.months
            day = other.day + self.days
            hour = other.hour + self.hours
            minute = other.minute + self.minutes
            second = other.second + self.seconds
            return other.replace(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        raise TypeError("Unsupported operand type(s) for +: 'relativedelta' and '{}'".format(type(other)))

    def __sub__(self, other):
        if isinstance(other, datetime.datetime):
            year = other.year - self.years
            month = other.month - self.months
            day = other.day - self.days
            hour = other.hour - self.hours
            minute = other.minute - self.minutes
            second = other.second - self.seconds
            return other.replace(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
        raise TypeError("Unsupported operand type(s) for -: 'relativedelta' and '{}'".format(type(other)))