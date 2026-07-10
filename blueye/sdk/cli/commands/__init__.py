"""First-party command registry for the `blueye` CLI.

Every built-in command lives in its own package under ``blueye/sdk/cli/commands/`` and
exposes a module-level ``COMMAND: CommandSpec``. Registering a new command means adding
it to :func:`all_commands` — nothing else in the CLI changes.

Invariants command packages must uphold:

- The package (and everything it imports at module level) must be importable with zero
  optional extras installed; heavy imports (onnx, rich, questionary, ...) belong inside
  ``run``. This keeps ``blueye --help`` working before the ``[cli]`` extra is installed.
- ``add_parser`` uses only argparse.
- User-facing failures raise :class:`blueye.sdk.cli.errors.CliError`; ``main`` turns
  them into a clean message and exit code 1.

The CommandSpec contract is also the intended payload for future pip-installable
plugins (a ``blueye.cli`` entry-point group): an external distribution would expose the
same object, and the registry would grow a second discovery source.
"""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CommandSpec:
    """One first-party `blueye` subcommand.

    Attributes:
        name: The subcommand name (e.g. "bundle-model").
        help: One-line description shown in ``blueye --help``.
        requires: Import names of optional dependencies that must be installed before
            ``run`` executes; ``main`` gates on these and prints install guidance.
        add_parser: Registers the subcommand's arguments on the root subparsers
            (argparse only, no optional imports).
        run: Executes the command and returns the process exit code.
    """

    name: str
    help: str
    requires: tuple[str, ...]
    add_parser: Callable[[argparse._SubParsersAction], None]
    run: Callable[[argparse.Namespace], int]


def all_commands() -> tuple[CommandSpec, ...]:
    """Return every built-in command, in the order shown in ``blueye --help``."""
    from .bundle_model import COMMAND as bundle_model_command
    from .models import COMMAND as models_command
    from .tools import COMMAND as tools_command

    return (bundle_model_command, models_command, tools_command)
