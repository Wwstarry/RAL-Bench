"""
mailpile.i18n
=============

A **very** small subset of the original i18n helper which only offers
a no-op translation function.  In the real Mailpile application this
module wires up the gettext catalogue and offers pluralisation helpers.
For the purposes of the benchmark we simply need a dummy passthrough so
that the rest of the code can safely do `from mailpile.i18n import _`.
"""
from __future__ import unicode_literals, absolute_import

try:
    import gettext

    # Attempt to hook into the default translations if they exist,
    # otherwise silently fall back to an identity function.
    _ = gettext.gettext
except Exception:  # pragma: no cover
    # No gettext support or catalogue not installed – fall back
    # to a dummy implementation that simply returns the input.
    def _(message):
        """Passthrough translation helper (identity function)."""
        return message


__all__ = ["_"]