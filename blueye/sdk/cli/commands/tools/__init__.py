"""The `blueye tools` command: manage third-party CLI tools."""

from __future__ import annotations

from .. import CommandSpec
from .command import add_parser, run

COMMAND = CommandSpec(
    name="tools",
    help="List, validate, install, and uninstall third-party CLI tools",
    requires=(),  # The bootstrap surface must run with zero optional extras.
    add_parser=add_parser,
    run=run,
)
