# mitmproxy - Minimal Implementation

A minimal, safe-to-evaluate subset of the mitmproxy project that implements the core API surfaces required for testing and validation.

## Features

- **HTTP Flow Abstractions**: HTTPFlow, HTTPRequest, HTTPResponse classes
- **Flow Management**: Base Flow class with metadata support
- **Addon System**: AddonManager for extensibility
- **CLI Tools**: mitmdump, mitmweb, and console frontends
- **Command Line Parsing**: Full argument parsing for mitmdump

## Installation

```bash
pip install -e .
```

## Usage

### mitmdump

```bash
mitmdump -l 127.0.0.1 -p 8080
mitmdump -m transparent
mitmdump -s addon.py
```

### API Usage

```python
from mitmproxy.http import HTTPFlow, HTTPRequest, HTTPResponse
from mitmproxy.addonmanager import AddonManager

# Create a flow
flow = HTTPFlow()
flow.request = HTTPRequest(method="GET", authority="example.com", path="/")
flow.response = HTTPResponse(status_code=200)

# Use addon manager
manager = AddonManager()
manager.add_option("my_option", str, "default")
manager.add_command("my_command", lambda: "result")
```

## Project Structure

```
mitmproxy/
├── __init__.py
├── flow.py              # Base flow abstractions
├── http.py              # HTTP flow types
├── addonmanager.py      # Addon management system
├── version.py           # Version info
├── tools/
│   ├── main.py          # Entry points
│   ├── dump.py          # mitmdump master
│   ├── cmdline.py       # CLI argument parsing
│   ├── mitmweb.py       # Web UI master
│   └── console.py       # Console UI master
├── addons/
│   ├── core.py          # Core addon
│   ├── proxyserver.py   # Proxy server addon
│   └── eventstore.py    # Event store addon
└── proxy/
    └── server.py        # Proxy server implementation
```

## Testing

```bash
pytest tests/
```

## API Compatibility

This implementation maintains API compatibility with the reference mitmproxy project for:

- Module layout and importability
- Core public API symbols (HTTPFlow, HTTPRequest, HTTPResponse, AddonManager)
- CLI argument parsing and help output
- Addon system interfaces

## Safety

This implementation does NOT perform:
- Real traffic interception
- Man-in-the-middle attacks
- Network operations
- TLS certificate generation

It is safe to evaluate and test.