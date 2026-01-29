# Requests Core API Test Suite

This repository contains comprehensive tests for the Python Requests library's core functionality, tested against a local HTTP server to avoid external network dependencies.

## Features Tested

- **requests.api**: High-level request helpers (get, post, put, delete)
- **requests.sessions**: Session lifecycle, cookie persistence, headers
- **requests.models**: Request/Response object preparation and inspection
- **requests.auth**: HTTP Basic authentication
- **requests.exceptions**: Error handling and exception taxonomy

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the tests:
```bash
python test_requests_core.py
```

## Test Coverage

The test suite includes:

- HTTP methods (GET, POST, PUT, DELETE)
- Session management with cookie persistence
- Request/Response object model inspection
- Basic authentication flows
- Exception handling for timeouts and connection errors
- Query parameter and header testing

## Local Server

Tests run against an embedded HTTP server that provides endpoints for:
- Echo functionality
- Cookie management
- Basic authentication
- Timeout testing
- Various HTTP methods

This ensures reliable, fast testing without external dependencies.