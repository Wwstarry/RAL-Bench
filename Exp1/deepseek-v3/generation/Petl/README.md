# Petl Light

A lightweight pure Python ETL library that provides core functionality compatible with the Petl project.

## Installation

```bash
pip install -e .
```

## Usage

```python
import petl

# Read CSV
table = petl.fromcsv('data.csv')

# Transform data
table = (table
    .convert('age', int)
    .select(lambda row: int(row[1]) > 18)  # Assuming age is at index 1
    .sort('age')
)

# Write to CSV
table.tocsv('output.csv')
```

## Features

- Lazy evaluation for memory efficiency
- CSV input/output
- Field conversions
- Row filtering and selection
- Sorting
- Table joins
- Dictionary to table conversion

## API Compatibility

This library aims to be API-compatible with the core functionality of Petl as used by common test suites.