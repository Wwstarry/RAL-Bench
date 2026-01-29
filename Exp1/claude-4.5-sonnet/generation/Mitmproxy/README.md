# mitmproxy

An interactive TLS-capable intercepting HTTP proxy for penetration testers and software developers.

## Features

- Intercept HTTP & HTTPS requests and responses
- Save complete HTTP conversations for later replay and analysis
- Replay the client-side of an HTTP conversation
- Replay HTTP responses of a previously recorded server
- Reverse proxy mode to forward traffic to a specified server
- Transparent proxy mode on macOS and Linux
- Make scripted changes to HTTP traffic using Python
- SSL/TLS certificates for interception are generated on the fly

## Installation

```bash
pip install mitmproxy
```

## Tools

mitmproxy comes with three tools:

- **mitmproxy**: An interactive console program for inspecting and modifying HTTP traffic
- **mitmdump**: A command-line version of mitmproxy for automated processing
- **mitmweb**: A web-based interface for mitmproxy

## Usage

### mitmdump

```bash
mitmdump
```

Start mitmdump on the default port (8080).

```bash
mitmdump -p 8888
```

Start mitmdump on port 8888.

```bash
mitmdump -w outfile
```

Start mitmdump and save all flows to a file.

### mitmproxy

```bash
mitmproxy
```

Start the interactive console interface.

### mitmweb

```bash
mitmweb
```

Start the web interface.

## Documentation

For more information, please visit [mitmproxy.org](https://mitmproxy.org).

## License

MIT License