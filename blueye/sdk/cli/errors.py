"""Shared CLI error types.

Standard library only, and imports nothing from the package — every CLI module may
depend on this one without creating an import cycle.
"""

from __future__ import annotations


class CliError(Exception):
    """A user-facing CLI error: printed as a message, never as a traceback."""
