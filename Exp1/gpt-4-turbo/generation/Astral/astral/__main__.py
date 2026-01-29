# astral/__main__.py

if __name__ == "__main__":
    from .location import LocationInfo
    from .sun import sun
    from datetime import date
    import sys

    if len(sys.argv) < 6:
        print("Usage: python -m astral <name> <region> <timezone> <latitude> <longitude>")
        sys.exit(1)
    name = sys.argv[1]
    region = sys.argv[2]
    timezone = sys.argv[3]
    latitude = float(sys.argv[4])
    longitude = float(sys.argv[5])
    loc = LocationInfo(name, region, timezone, latitude, longitude)
    today = date.today()
    print(f"Location: {loc}")
    print("Sun events for today:")
    events = sun(loc.observer, today)
    for k, v in events.items():
        print(f"  {k}: {v}")