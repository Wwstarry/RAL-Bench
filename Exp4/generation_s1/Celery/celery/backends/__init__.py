from __future__ import annotations

from .memory import MemoryBackend


def get_backend_by_url(url: str):
    # Minimal: only memory backend supported
    if not url or url.startswith("memory://"):
        return MemoryBackend()
    # Fallback to memory for unknown schemes in this minimal implementation
    return MemoryBackend()