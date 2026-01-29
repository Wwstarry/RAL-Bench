from celery.backends.memory import MemoryBackend

def get_backend(backend_url):
    """Get a backend instance based on the URL."""
    if backend_url.startswith("memory://"):
        return MemoryBackend()
    raise ValueError(f"Unsupported backend: {backend_url}")