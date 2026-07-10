"""The `blueye logs` command: list and download dive logs from the drone."""

from __future__ import annotations

from .. import CommandSpec
from .command import add_parser, run

COMMAND = CommandSpec(
    name="logs",
    help="List and download dive logs from the drone",
    requires=(),  # rich/questionary are core SDK dependencies; --mcap gates at runtime.
    add_parser=add_parser,
    run=run,
)
