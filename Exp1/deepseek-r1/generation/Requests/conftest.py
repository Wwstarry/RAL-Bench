import pytest
from pytest_httpbin import certs

@pytest.fixture(scope='session')
def httpbin_secure(request):
    return certs.where()

@pytest.fixture
def httpbin(httpbin, httpbin_secure):
    return httpbin