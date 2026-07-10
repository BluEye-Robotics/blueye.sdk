"""The `blueye models` command: manage the CV models installed on the drone."""

from __future__ import annotations

from .. import CommandSpec
from .command import add_parser, run

COMMAND = CommandSpec(
    name="models",
    help="Manage the CV model packages installed on the drone",
    requires=("rich", "questionary"),
    add_parser=add_parser,
    run=run,
)
