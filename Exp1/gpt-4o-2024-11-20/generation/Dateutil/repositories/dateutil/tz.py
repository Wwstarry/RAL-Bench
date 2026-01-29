import datetime

class tzutc(datetime.tzinfo):
    def utcoffset(self, dt):
        return datetime.timedelta(0)

    def dst(self, dt):
        return datetime.timedelta(0)

    def tzname(self, dt):
        return "UTC"

UTC = tzutc()

def gettz(name):
    if name == "UTC":
        return UTC
    raise ValueError(f"Unknown timezone: {name}")