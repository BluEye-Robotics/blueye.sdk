"""Entry point for the `blueye` command line interface.

Only the standard library may be imported at module level: the umbrella command and
`--help` must work (and print install guidance) when the optional `[cli]` extra is not
installed. First-party commands come from the registry in
:mod:`blueye.sdk.cli.commands`; third-party tools are discovered from the tools
directory (see :mod:`blueye.sdk.cli.external`) and dispatched before argparse runs.
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import deps
from .commands import CommandSpec, all_commands

# Back-compat re-export; the canonical location is blueye.sdk.cli.errors.
from .errors import CliError  # noqa: F401

logger = logging.getLogger(__name__)


def _build_parser(
    commands: dict[str, CommandSpec], tools_epilog: str | None
) -> argparse.ArgumentParser:
    """Build the root `blueye` parser with all first-party commands registered."""
    parser = argparse.ArgumentParser(
        prog="blueye",
        description="Command line tools for Blueye underwater drones.",
        epilog=tools_epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    for spec in commands.values():
        spec.add_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the `blueye` CLI.

    Args:
        argv: Argument list to parse; defaults to ``sys.argv[1:]``.

    Returns:
        The process exit code (0 success, 1 user-facing error, 2 missing dependencies,
        130 interrupted; third-party tools propagate their own exit code).
    """
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    argv = list(sys.argv[1:] if argv is None else argv)

    commands = {spec.name: spec for spec in all_commands()}

    from .external import discovery, execution

    tools = discovery.discover_tools(frozenset(commands))

    # Third-party tools bypass argparse entirely: their arguments belong to the tool,
    # and argparse's REMAINDER cannot forward leading-dash arguments from a subparser.
    # Builtins always win a name collision (checked first). Invocation is strictly
    # `blueye <tool-name> args...` — root-level flags before the tool name are not
    # supported.
    if argv and not argv[0].startswith("-") and argv[0] not in commands and argv[0] in tools:
        try:
            return execution.run_tool(tools[argv[0]], argv[1:])
        except KeyboardInterrupt:
            print("\nCancelled.", file=sys.stderr)
            return 130

    parser = _build_parser(commands, discovery.format_tools_epilog(tools))
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    spec = commands[args.command]
    missing = deps.missing(spec.requires)
    if missing:
        deps.print_install_guidance(missing)
        return 2

    try:
        return spec.run(args)
    except CliError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130
