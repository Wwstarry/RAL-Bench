# Minimal Fail2Ban Implementation

This is a minimal, safe-to-evaluate subset of Fail2Ban focused on core API surface and offline testing capabilities.

## Features

- **Jail management**: Coordinate filters and actions for log monitoring
- **IP validation**: Utilities for IP address parsing and validation  
- **Regex matching**: Pattern-based log line analysis
- **Safe operation**: No real firewall modifications or daemon operations

## Safety Guarantees

- ✅ No firewall rule modifications
- ✅ No daemon processes started
- ✅ No root privileges required
- ✅ All operations are offline and testable

## Usage

### Testing Regex Patterns

```bash
# Test a pattern against a log file
python bin/fail2ban-regex "Failed password for .* from <HOST>" /var/log/auth.log

# Test with stdin
cat /var/log/auth.log | python bin/fail2ban-regex "Authentication failure"
```

### Testing Jail Functionality

```python
from fail2ban.server.jail import Jail
from fail2ban.server.filter import Filter

# Create a jail for SSH failures
jail = Jail("sshd")
filter_obj = Filter("ssh", r"Failed password for .* from <HOST>")
jail.addFilter(filter_obj)

# Process log lines
result = jail.processLine("Failed password for root from 192.168.1.1", 1234567890.0)
if result:
    jail.banIP(result['ip'])  # Simulated ban
```

## API Reference

### Core Classes

- `Jail`: Manages filters and actions for monitoring
- `Filter`: Defines patterns to match in log files

### Utility Functions

- `isValidIP(ip)`: Validate IP address format
- `searchIP(text)`: Extract IP addresses from text

## Testing

Run the test suite:

```bash
python -m unittest tests/test_minimal_fail2ban.py
```

## Limitations

This implementation does NOT:
- Modify firewall rules
- Start background daemons  
- Require root privileges
- Support all Fail2Ban features

It's designed for API validation and testing pattern matching behavior safely.