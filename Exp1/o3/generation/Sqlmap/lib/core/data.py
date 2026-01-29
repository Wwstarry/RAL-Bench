"""
`lib.core.data` – shared global runtime state.

The original sqlmap project stores almost all internally mutable global
state here so that all parts of the code base can import it without
creating circular dependencies. We replicate only the pieces the tests
expect: `cmdLineOptions`, `conf` and `kb`.
"""
import types

# Will be set by `lib.parse.cmdline.cmdLineParser`
cmdLineOptions = None          # type: ignore

# `conf` and `kb` are SimpleNamespace instances so they can be written to
# using attribute access (`conf.url`, `kb.techniques`, …) just like sqlmap.
conf = types.SimpleNamespace()  # Configuration options resolved/merged.
kb = types.SimpleNamespace()    # Knowledge base – runtime collected info.