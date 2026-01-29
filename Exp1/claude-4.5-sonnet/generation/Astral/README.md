# Astral

A pure Python library for calculating sun and moon times.

## Features

- Calculate sunrise, sunset, dawn, dusk, and solar noon
- Calculate moon phase
- Timezone-aware datetime results
- Simple API

## Installation

```bash
pip install -e .
```

## Usage

```python
from astral import LocationInfo
from astral.sun import sun, sunrise, sunset
from astral.moon import phase
from datetime import date
import pytz

# Create a location
city = LocationInfo("London", "England", "Europe/London", 51.5, -0.116)

# Get all solar times for today
s = sun(city.observer, date=date.today(), tzinfo=city.timezone)
print(f"Dawn:    {s['dawn']}")
print(f"Sunrise: {s['sunrise']}")
print(f"Noon:    {s['noon']}")
print(f"Sunset:  {s['sunset']}")
print(f"Dusk:    {s['dusk']}")

# Get specific times
sunrise_time = sunrise(city.observer, tzinfo=city.timezone)
sunset_time = sunset(city.observer, tzinfo=city.timezone)

# Get moon phase
moon_phase = phase(date.today())
print(f"Moon phase: {moon_phase}")
```

## API

### LocationInfo

Represents a location with geographic and timezone information.

```python
LocationInfo(name, region, timezone, latitude, longitude)
```

### astral.sun

- `sun(observer, date=None, tzinfo=None)` - Returns dict with dawn, sunrise, noon, sunset, dusk
- `sunrise(observer, date=None, tzinfo=None)` - Returns sunrise time
- `sunset(observer, date=None, tzinfo=None)` - Returns sunset time
- `noon(observer, date=None, tzinfo=None)` - Returns solar noon time
- `dawn(observer, date=None, tzinfo=None)` - Returns dawn time (civil twilight)
- `dusk(observer, date=None, tzinfo=None)` - Returns dusk time (civil twilight)

### astral.moon

- `phase(date=None)` - Returns moon phase (0-28, where 0=New Moon, 14=Full Moon)

## License

MIT