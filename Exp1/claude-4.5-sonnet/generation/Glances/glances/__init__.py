"""
Glances - A cross-platform system monitoring tool
"""

__version__ = "3.4.0"

from glances.stats import GlancesStats

__all__ = ['GlancesStats', '__version__']
</file:

<file:name=glances/__main__.py>
"""
Main entry point for glances CLI
"""

import sys
from glances.cli import main

if __name__ == '__main__':
    sys.exit(main())
</file:

<file:name=glances/cli.py>
"""
Command-line interface for glances
"""

import sys
import argparse
from glances import __version__
from glances.stats import GlancesStats


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='glances',
        description='Glances - A cross-platform system monitoring tool'
    )
    
    parser.add_argument(
        '-V', '--version',
        action='version',
        version=f'Glances v{__version__}'
    )
    
    parser.add_argument(
        '--stdout-csv',
        metavar='FIELDS',
        dest='stdout_csv',
        help='Display stats in CSV format (comma-separated field list)'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle --stdout-csv
    if args.stdout_csv is not None:
        return handle_stdout_csv(args.stdout_csv)
    
    # Default behavior (no action specified)
    parser.print_help()
    return 0


def handle_stdout_csv(fields_str):
    """Handle --stdout-csv option"""
    if not fields_str:
        sys.stderr.write("Error: --stdout-csv requires a field list\n")
        return 1
    
    # Parse field list
    fields = [f.strip() for f in fields_str.split(',')]
    
    # Validate fields
    stats = GlancesStats()
    valid_fields = stats.get_valid_fields()
    
    for field in fields:
        if field not in valid_fields:
            sys.stderr.write(f"Error: Unknown field '{field}'\n")
            return 1
    
    # Get stats
    try:
        values = stats.get_csv_values(fields)
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        return 1
    
    # Output CSV
    print(','.join(str(v) for v in values))
    return 0
</file:

<file:name=glances/stats.py>
"""
Statistics collection for glances
"""

import time
import psutil


class GlancesStats:
    """Collect and provide system statistics"""
    
    def __init__(self):
        self._valid_fields = {
            'now',
            'cpu.user',
            'cpu.total',
            'mem.used',
            'load'
        }
    
    def get_valid_fields(self):
        """Return set of valid field names"""
        return self._valid_fields
    
    def get_csv_values(self, fields):
        """Get values for the specified fields in CSV format"""
        values = []
        
        for field in fields:
            if field == 'now':
                values.append(self._get_now())
            elif field == 'cpu.user':
                values.append(self._get_cpu_user())
            elif field == 'cpu.total':
                values.append(self._get_cpu_total())
            elif field == 'mem.used':
                values.append(self._get_mem_used())
            elif field == 'load':
                values.append(self._get_load())
            else:
                raise ValueError(f"Unknown field: {field}")
        
        return values
    
    def _get_now(self):
        """Get current timestamp"""
        return time.time()
    
    def _get_cpu_user(self):
        """Get CPU user percentage"""
        cpu_times = psutil.cpu_times_percent(interval=0.1)
        return cpu_times.user
    
    def _get_cpu_total(self):
        """Get total CPU percentage"""
        return psutil.cpu_percent(interval=0.1)
    
    def _get_mem_used(self):
        """Get used memory in bytes"""
        mem = psutil.virtual_memory()
        return mem.used
    
    def _get_load(self):
        """Get system load average (1 minute)"""
        try:
            # getloadavg returns (1min, 5min, 15min)
            load = psutil.getloadavg()[0]
            return load
        except (AttributeError, OSError):
            # getloadavg not available on Windows
            # Return CPU percent as fallback
            return psutil.cpu_percent(interval=0.1)
</file:

<file:name=setup.py>
"""
Setup script for glances
"""

from setuptools import setup, find_packages
from glances import __version__

setup(
    name='glances',
    version=__version__,
    description='A cross-platform system monitoring tool',
    author='Glances Team',
    packages=find_packages(),
    install_requires=[
        'psutil>=5.0.0',
    ],
    entry_points={
        'console_scripts': [
            'glances=glances.cli:main',
        ],
    },
    python_requires='>=3.6',
)
</file:

<file:name=README.md>
# Glances

A cross-platform system monitoring tool.

## Installation

```bash
pip install -e .
```

## Usage

### Display help
```bash
python -m glances --help
```

### Display version
```bash
python -m glances --version
```

### CSV output
```bash
python -m glances --stdout-csv now,cpu.user,mem.used,load
```

## Supported CSV Fields

- `now` - Current timestamp
- `cpu.user` - CPU user percentage
- `cpu.total` - Total CPU percentage
- `mem.used` - Used memory in bytes
- `load` - System load average (1 minute)
</file:

<file:name=requirements.txt>
psutil>=5.0.0