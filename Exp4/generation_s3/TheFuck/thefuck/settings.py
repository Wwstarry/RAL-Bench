from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """
    Minimal settings container. Tests may pass a dict instead; code accepts both.

    Attributes:
        no_interactive: never prompt user. Defaults True to keep tests unattended.
        debug: emit debug output to stderr (best-effort).
        max_suggestions: cap number of printed/returned suggestions.
    """

    no_interactive: bool = True
    debug: bool = False
    max_suggestions: int = 5


def as_settings(settings: object | None) -> Settings:
    if settings is None:
        return Settings()
    if isinstance(settings, Settings):
        return settings
    if isinstance(settings, dict):
        return Settings(
            no_interactive=bool(settings.get("no_interactive", True)),
            debug=bool(settings.get("debug", False)),
            max_suggestions=int(settings.get("max_suggestions", 5)),
        )
    # Fallback: try attribute access
    return Settings(
        no_interactive=bool(getattr(settings, "no_interactive", True)),
        debug=bool(getattr(settings, "debug", False)),
        max_suggestions=int(getattr(settings, "max_suggestions", 5)),
    )