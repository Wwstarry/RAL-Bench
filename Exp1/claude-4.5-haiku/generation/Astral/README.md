# Astral

A pure Python sun and moon time calculation library.

## Installation

```bash
pip install -e .
```

## Usage

### Sun Times

```python
from astral import LocationInfo
from datetime import datetime
import pytz

# Create a location
loc = LocationInfo("London", "England", 51.5074, -0.1278, "Europe/London")

# Get sun times
from astral.sun import sun

times = sun(loc.observer, datetime(2023, 1, 1), loc.tzinfo())
print(f"Sunrise: {times['sunrise']}")
print(f"Sunset: {times['sunset']}")
```

### Moon Phase

```python
from astral.moon import phase
from datetime import datetime

# Get lunar phase (0 to 1)
lunar_phase = phase(datetime(2023, 1, 1))
print(f"Lunar phase: {lunar_phase}")
```

## API

### LocationInfo

Represents a named location with geographic and timezone information.

**Attributes:**
- `name`: Location name
- `region`: Region/country
- `latitude`: Latitude in degrees
- `longitude`: Longitude in degrees
- `timezone`: Timezone string (e.g., "Europe/London")
- `elevation`: Elevation in meters (optional)
- `observer`: Property returning an Observer object

### Sun Functions

#### `sun(observer, date=None, tzinfo=None)`

Calculate sun times for a given observer and date.

**Returns:** Dictionary with keys 'dawn', 'sunrise', 'noon', 'sunset', 'dusk'

#### `sunrise(observer, date=None, tzinfo=None)`

Calculate sunrise time.

#### `sunset(observer, date=None, tzinfo=None)`

Calculate sunset time.

### Moon Functions

#### `phase(date)`

Calculate lunar phase (0 to 1) for a given date.