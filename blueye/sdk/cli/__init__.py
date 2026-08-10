"""Command line interface for the Blueye SDK.

This package provides the `blueye` console script. It is deliberately kept out of
`blueye.sdk.__init__` so the SDK itself imports without the optional `[cli]` extra
installed. Only the standard library may be imported at module level here — the CLI
must be able to start (and print dependency guidance) when the extra is missing.
"""

from .main import main

__all__ = ["main"]
