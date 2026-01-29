# mitmproxy - Minimal Implementation

This is a minimal, safe-to-evaluate implementation of the mitmproxy API surface.

## Purpose

This implementation provides the core API surfaces required for compatibility testing without performing actual traffic interception or man-in-the-middle attacks.

## Features

- API-compatible modules: `mitmproxy.http`, `mitmproxy.flow`, `mitmproxy.addonmanager`
- CLI entry points: `mitmdump` command line tool
- Safe for evaluation (no network interception capabilities)

## Usage

```bash
mitmdump --help
```

## Safety Note

This implementation does not perform any network interception or man-in-the-middle attacks. It only provides the API surface required for compatibility testing.