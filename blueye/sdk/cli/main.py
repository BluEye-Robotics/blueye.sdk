"""Entry point for the `blueye` command line interface.

Only the standard library may be imported at module level: the umbrella command and
`--help` must work (and print install guidance) when the optional `[cli]` extra is not
installed. Subcommand implementations are imported lazily after the dependency gate.
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import deps

logger = logging.getLogger(__name__)


class CliError(Exception):
    """A user-facing CLI error: printed as a message, never as a traceback."""


def _build_parser() -> argparse.ArgumentParser:
    """Build the root `blueye` parser with all subcommands registered."""
    parser = argparse.ArgumentParser(
        prog="blueye",
        description="Command line tools for Blueye underwater drones.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # Subcommand argument definitions live in their own modules, but only argument
    # *definitions* — anything importing optional dependencies stays behind the gate in
    # main(). bundle_model.add_parser only uses argparse.
    from . import bundle_model

    bundle_model.add_parser(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the `blueye` CLI.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code (0 success, 1 user-facing error, 2 missing dependencies,
        130 interrupted).
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    missing = deps.missing_cli_deps()
    if missing:
        deps.print_install_guidance(missing)
        return 2

    try:
        if args.command == "bundle-model":
            from . import bundle_model

            return bundle_model.run(args)
    except CliError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130

    parser.print_help()
    return 0
