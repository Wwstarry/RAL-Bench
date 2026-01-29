# Requests Library Test Suite

This repository contains a comprehensive test suite for the Python `requests` library, focusing on core public APIs.

## Overview

The test suite evaluates the following core modules and interfaces:

- **requests.api**: High-level request helpers (get, post, put, delete, etc.)
- **requests.sessions**: Session lifecycle, cookies, and adapters
- **requests.models**: Request/Response objects and preparation
- **requests.auth**: Basic authentication helpers
- **requests.exceptions**: Request error taxonomy

## Features

- Local HTTP server for testing (no external network dependencies)
- Comprehensive coverage of core APIs
- Integration tests combining multiple features
- Clean, well-organized test structure

## Installation

```bash
pip install -e .
pip install -e ".[dev]"
```

## Running Tests

Run all tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov=tests
```

Run specific test file:
```bash
pytest tests/test_api.py
```

Run specific test:
```bash
pytest tests/test_api.py::TestRequestsAPI::test_get_request
```

## Test Structure

- `tests/conftest.py`: Pytest configuration and HTTP server fixture
- `tests/test_api.py`: High-level API tests (get, post, put, delete, etc.)
- `tests/test_sessions.py`: Session management and cookie tests
- `tests/test_models.py`: Request/Response object tests
- `tests/test_auth.py`: Authentication tests
- `tests/test_exceptions.py`: Exception handling tests
- `tests/test_integration.py`: Integration tests combining features

## Test Coverage

### API Tests
- GET, POST, PUT, DELETE, HEAD, OPTIONS requests
- Query parameters
- Custom headers
- Timeouts
- Redirect handling

### Session Tests
- Session creation and lifecycle
- Cookie persistence
- Header persistence
- Context manager usage
- Custom adapters
- SSL verification settings

### Model Tests
- Response status codes, headers, content
- JSON parsing
- URL handling
- Redirect history
- Request preparation
- Response properties (ok, is_redirect)

### Auth Tests
- Basic authentication
- Authentication with tuples
- Authentication headers
- Session-level authentication

### Exception Tests
- Exception hierarchy
- HTTPError with response objects
- raise_for_status() behavior
- Invalid URL handling

### Integration Tests
- Session with auth and cookies
- Multiple requests with headers and auth
- Complete request-response cycles
- Custom adapter configuration
- Prepared request execution
- Error handling with sessions
- Redirect following with auth