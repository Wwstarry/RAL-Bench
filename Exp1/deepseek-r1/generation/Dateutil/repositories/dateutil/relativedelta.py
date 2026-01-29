class relativedelta:
    def __init__(self, years=0, months=0, days=0, 
                 hours=0, minutes=0, seconds=0, 
                 year=None, month=None, day=None):
        self.years = years
        self.months = months
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.seconds = seconds
        self.year = year
        self.month = month
        self.day = day

    def __add__(self, other):
        if not isinstance(other, datetime.datetime):
            raise TypeError("Only datetime supported")
        
        # Apply relative components
        year = other.year + self.years
        month = other.month + self.months
        if month > 12:
            year += (month - 1) // 12
            month = (month - 1) % 12 + 1
        
        # Create new datetime
        dt = other.replace(
            year=year,
            month=month,
            day=min(other.day, self.day or other.day),
            hour=other.hour + self.hours,
            minute=other.minute + self.minutes,
            second=other.second + self.seconds
        )
        
        # Apply absolute components
        if self.year is not None:
            dt = dt.replace(year=self.year)
        if self.month is not None:
            dt = dt.replace(month=self.month)
        if self.day is not None:
            dt = dt.replace(day=self.day)
        
        # Add days separately
        if self.days:
            dt += datetime.timedelta(days=self.days)
        
        return dt