# Minimal mitmproxy Implementation

This is a minimal, safe-to-evaluate implementation of mitmproxy's public API surface.

## Purpose

This implementation provides the core API interfaces required for compatibility testing without performing actual traffic interception or man-in-the-middle attacks.

## API Coverage

The following key modules are implemented:

- `mitmproxy.http`: HTTP message types (Request, Response, HTTPFlow, Headers)
- `mitmproxy.flow`: Flow base abstractions
- `mitmproxy.addonmanager`: AddonManager for options/commands integration
- `mitmproxy.tools.main.mitmdump`: CLI entry function
- `mitmproxy.tools.dump.DumpMaster`: mitmdump master class
- `mitmproxy.tools.cmdline.mitmdump`: Argument specification and parsing

## Safety Note

This implementation does NOT perform any network interception, traffic manipulation, or security testing. It only provides the API interfaces needed for compatibility validation.

## Installation

```bash
pip install -e .
```

## Usage

```bash
mitmdump --help
mitmdump --version
```

## License

MIT