"""Implementation of the `blueye tools` subcommands.

Standard library only — this command is the bootstrap surface for the third-party tool
mechanism, so it must work before (or without) the ``[cli]`` extra.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
from pathlib import Path

from ...errors import CliError
from ...external import discovery, metadata

logger = logging.getLogger(__name__)


def add_parser(subparsers) -> None:
    """Register the ``tools`` subcommand and its sub-subcommands."""
    parser = subparsers.add_parser(
        "tools",
        help="List, validate, install, and uninstall third-party CLI tools",
        description=(
            "Manage third-party blueye tools: single-file Python scripts with PEP 723 "
            "inline metadata, discovered from the tools directory and run as "
            "`blueye <tool-name> ...`. See the 'Extending the blueye CLI' documentation "
            "for how to write one."
        ),
    )
    tools_subparsers = parser.add_subparsers(dest="tools_command", metavar="ACTION")

    tools_subparsers.add_parser("list", help="List built-in commands and discovered tools")

    validate = tools_subparsers.add_parser("validate", help="Validate a tool script's metadata")
    validate.add_argument("script", help="Path to the tool script (.py)")

    install = tools_subparsers.add_parser(
        "install", help="Validate a tool script and copy it into the tools directory"
    )
    install.add_argument("script", help="Path to the tool script (.py)")
    install.add_argument(
        "--force", action="store_true", help="Replace an already-installed tool of the same name"
    )

    uninstall = tools_subparsers.add_parser(
        "uninstall", help="Remove an installed tool from the tools directory"
    )
    uninstall.add_argument("name", help="The tool name (as shown by `blueye tools list`)")

    tools_subparsers.add_parser("dir", help="Print the resolved tools directory")


def run(args: argparse.Namespace) -> int:
    """Dispatch the tools sub-subcommand."""
    action = getattr(args, "tools_command", None)
    if action == "list":
        return _run_list()
    if action == "validate":
        return _run_validate(Path(args.script).expanduser())
    if action == "install":
        return _run_install(Path(args.script).expanduser(), force=args.force)
    if action == "uninstall":
        return _run_uninstall(args.name)
    if action == "dir":
        return _run_dir()
    print("Usage: blueye tools {list,validate,install,uninstall,dir}", file=sys.stderr)
    return 1


def _builtin_names() -> frozenset[str]:
    from .. import all_commands

    return frozenset(spec.name for spec in all_commands())


def _run_list() -> int:
    """Print built-in commands and every scanned tool, valid or not."""
    from .. import all_commands

    directory = discovery.tools_dir()
    print(f"Tools directory: {directory} ({discovery.tools_dir_source()})")
    print()

    rows: list[tuple[str, str, str]] = []
    for spec in all_commands():
        rows.append((spec.name, "built-in", spec.help))
    for tool in discovery.scan_tools_dir(_builtin_names()):
        if tool.metadata is None:
            rows.append((tool.path.name, tool.path.name, f"(invalid metadata: {tool.error})"))
        elif tool.shadowed_by is not None:
            rows.append((tool.metadata.name, tool.path.name, f"(shadowed by {tool.shadowed_by})"))
        else:
            rows.append((tool.metadata.name, tool.path.name, tool.metadata.description))

    name_width = max(len(row[0]) for row in rows)
    source_width = max(len(row[1]) for row in rows)
    print(f"{'NAME'.ljust(name_width)}  {'SOURCE'.ljust(source_width)}  DESCRIPTION")
    for name, source, description in rows:
        print(f"{name.ljust(name_width)}  {source.ljust(source_width)}  {description}")
    return 0


def _run_validate(script: Path) -> int:
    """Run every metadata check on a script, printing one line per check."""
    failures = 0

    def check(label: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        status = "ok" if ok else "error"
        suffix = f": {detail}" if detail else ""
        print(f"{status}: {label}{suffix}")
        if not ok:
            failures += 1

    if not script.is_file():
        print(f"error: no such file: {script}")
        return 1

    source = script.read_text(encoding="utf-8", errors="replace")
    try:
        block = metadata.extract_script_block(source)
    except metadata.MetadataError as error:
        check("PEP 723 script block", False, str(error))
        return 1
    check("PEP 723 script block", block is not None, "" if block else "no block found")
    if block is None:
        return 1

    try:
        parsed = metadata.parse_tool_metadata(source)
    except metadata.MetadataError as error:
        check("[tool.blueye] metadata", False, str(error))
        return 1
    check("[tool.blueye] metadata", True)
    check(f"tool name '{parsed.name}'", True)
    check("description", True)
    if parsed.parsed_with_fallback:
        print(
            "note: parsed with the limited fallback parser (install the [cli] extra "
            "for full TOML support on Python 3.10)"
        )

    collision = parsed.name in _builtin_names()
    check(
        "no collision with a built-in command",
        not collision,
        f"'{parsed.name}' is a built-in command" if collision else "",
    )
    if parsed.min_sdk_version is not None:
        well_formed = all(part.isdigit() for part in parsed.min_sdk_version.split("."))
        check(
            f"min-sdk-version '{parsed.min_sdk_version}'",
            well_formed,
            "" if well_formed else "must be dotted integers (e.g. 2.7.0)",
        )
    if parsed.has_dependencies:
        print("note: script declares dependencies; it will run via `uv run` when available")

    return 0 if failures == 0 else 1


def _run_install(script: Path, force: bool) -> int:
    """Validate a script and copy it into the tools directory as <name>.py."""
    if not script.is_file():
        raise CliError(f"No such file: {script}")
    try:
        parsed = metadata.parse_tool_metadata(script.read_text(encoding="utf-8"))
    except metadata.MetadataError as error:
        raise CliError(
            f"{script.name} is not a valid blueye tool: {error}. "
            "Run `blueye tools validate` for details."
        ) from error
    if parsed.name in _builtin_names():
        raise CliError(f"'{parsed.name}' collides with a built-in command — rename the tool.")

    directory = discovery.tools_dir()
    destination = directory / f"{parsed.name}.py"
    if destination.exists() and not force:
        raise CliError(f"{destination} already exists (use --force to replace it).")

    directory.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, destination)
    print(f"Installed '{parsed.name}' -> {destination}")
    print(f"Run it with: blueye {parsed.name}")
    return 0


def _run_uninstall(name: str) -> int:
    """Remove an installed tool by name."""
    directory = discovery.tools_dir()
    target = directory / f"{name}.py"
    if not target.is_file():
        # Hand-copied files may have a file name that differs from the tool name.
        target = None
        for tool in discovery.scan_tools_dir():
            if tool.metadata is not None and tool.metadata.name == name:
                target = tool.path
                break
        if target is None:
            installed = sorted(
                tool.metadata.name
                for tool in discovery.scan_tools_dir()
                if tool.metadata is not None
            )
            listing = ", ".join(installed) if installed else "none installed"
            raise CliError(f"No tool named '{name}' ({listing}).")

    target.unlink()
    print(f"Uninstalled '{name}' ({target})")
    return 0


def _run_dir() -> int:
    """Print the resolved tools directory (stdout is script-friendly)."""
    directory = discovery.tools_dir()
    print(directory)
    annotation = discovery.tools_dir_source()
    if not directory.exists():
        annotation += "; does not exist yet"
    print(f"({annotation})", file=sys.stderr)
    return 0
