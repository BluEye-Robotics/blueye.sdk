"""Implementation of the `blueye logs` subcommands.

Follows the documented log workflow (docs/logs/listing-and-downloading.md): connect to
the drone **as an observer** (taking no control), read the binary log index from
`drone.logs`, and download `.bez` files with `LogFile.download`. `convert` works on
already-downloaded files and never touches the drone. Legacy CSV logs are not covered
— use `drone.legacy_logs` from the SDK for those.

Argument definitions are stdlib-only; rich/questionary/blueye.sdk imports happen
inside `run` (after the dependency gate).
"""

from __future__ import annotations

import argparse
import datetime
import logging
import sys
from pathlib import Path

from ...errors import CliError
from .._common import drone_options_parser, friendly_errors

logger = logging.getLogger(__name__)


def _add_filter_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dives-only", action="store_true", help="Only logs classified as dives")
    parser.add_argument(
        "--since", metavar="YYYY-MM-DD", help="Only logs starting on or after this date"
    )
    parser.add_argument(
        "--until", metavar="YYYY-MM-DD", help="Only logs starting on or before this date"
    )


def add_parser(subparsers) -> None:
    """Register the ``logs`` subcommand and its sub-subcommands."""
    common = drone_options_parser(timeout_default=10.0)

    parser = subparsers.add_parser(
        "logs",
        parents=[common],
        help="List, download, and convert dive logs",
        description=(
            "List and download the drone's binary dive logs (.bez), and convert them "
            "to .mcap for Foxglove. Drone actions connect as an observer, taking no "
            "control. Run without an action on a terminal to pick logs interactively."
        ),
    )
    _add_filter_options(parser)
    actions = parser.add_subparsers(dest="logs_command", metavar="ACTION")

    list_parser = actions.add_parser("list", parents=[common], help="List the logs on the drone")
    _add_filter_options(list_parser)

    download = actions.add_parser("download", parents=[common], help="Download logs from the drone")
    download.add_argument("names", nargs="*", help="Log names to download")
    download.add_argument(
        "-o", "--output", default=".", help="Destination directory (default: current)"
    )
    download.add_argument(
        "--latest",
        type=int,
        metavar="N",
        help="Download the N most recent logs",
    )
    download.add_argument("--all", action="store_true", help="Download every log")
    download.add_argument(
        "--mcap",
        action="store_true",
        help="Also convert each downloaded log to .mcap (for Foxglove)",
    )
    _add_filter_options(download)

    convert = actions.add_parser(
        "convert",
        help="Convert already-downloaded .bez logs to .mcap (local, no drone needed)",
    )
    convert.add_argument("files", nargs="+", help="Paths to .bez files")
    convert.add_argument(
        "-o", "--output", help="Destination directory (default: next to each input file)"
    )


def _connect(args):
    """Connect to the drone as an observer and return the Drone object."""
    from blueye.sdk import Drone

    return friendly_errors(
        lambda: Drone(ip=args.drone_ip, timeout=args.timeout, connect_as_observer=True)
    )


def _parse_date(value: str, flag: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(value)
    except ValueError as error:
        raise CliError(f'{flag} must be a date like "2026-06-01", got "{value}"') from error


def _filter_logs(args, log_files) -> list:
    """Apply the --dives-only/--since/--until filters."""
    filtered = list(log_files)
    if getattr(args, "dives_only", False):
        filtered = [log for log in filtered if log.is_dive]
    since = getattr(args, "since", None)
    if since:
        since_date = _parse_date(since, "--since")
        filtered = [log for log in filtered if log.start_time.date() >= since_date]
    until = getattr(args, "until", None)
    if until:
        until_date = _parse_date(until, "--until")
        filtered = [log for log in filtered if log.start_time.date() <= until_date]
    return filtered


def _log_rows(logs, args) -> list:
    """The drone's logs, filtered and sorted descending alphabetically."""
    log_files = friendly_errors(lambda: list(logs))
    return sorted(_filter_logs(args, log_files), key=lambda log: log.name, reverse=True)


#: Column widths for the interactive table rows (monospace-aligned).
_NAME_WIDTH = 36
_TIME_WIDTH = 18
_SIZE_WIDTH = 10


def _format_row(log) -> str:
    from blueye.sdk.logs import human_readable_filesize

    return (
        f"{log.name.ljust(_NAME_WIDTH)}"
        f"{log.start_time.strftime('%d. %b %Y %H:%M').ljust(_TIME_WIDTH)}"
        f"{human_readable_filesize(log.filesize).ljust(_SIZE_WIDTH)}"
        f"{'dive' if log.is_dive else ''}"
    )


def _print_logs_table(console, log_files) -> None:
    from rich.table import Table

    from blueye.sdk.logs import human_readable_filesize

    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    for column in ("NAME", "TIME", "MAX DEPTH", "SIZE", "DIVE"):
        table.add_column(column)
    for log in log_files:
        table.add_row(
            log.name,
            log.start_time.strftime("%d. %b %Y %H:%M"),
            f"{log.max_depth_magnitude} m",
            human_readable_filesize(log.filesize),
            "yes" if log.is_dive else "[dim]no[/dim]",
        )
    console.print(table)


def _ensure_mcap_support() -> None:
    """Gate the .mcap paths on their optional dependency, with install guidance."""
    from ... import deps

    missing = deps.missing(("mcap_protobuf",))
    if missing:
        deps.print_install_guidance(missing)
        raise CliError("Converting to .mcap requires the mcap-protobuf-support package.")


def _download_logs(
    console, log_files, output_dir: Path, timeout: float, convert_mcap: bool = False
) -> None:
    from blueye.sdk.logs import human_readable_filesize

    if convert_mcap:
        _ensure_mcap_support()
        from .mcap import convert_bez_to_mcap

    output_dir.mkdir(parents=True, exist_ok=True)
    for log in log_files:
        with console.status(f"[cyan]Downloading {log.name}..."):
            friendly_errors(lambda: log.download(output_path=output_dir, timeout=timeout))
        console.print(
            f"Downloaded {log.name}.bez ({human_readable_filesize(log.filesize)}) "
            f"to {output_dir}"
        )
        if convert_mcap:
            bez_path = output_dir / f"{log.name}.bez"
            mcap_path = output_dir / f"{log.name}.mcap"
            with console.status(f"[cyan]Converting {log.name} to .mcap..."):
                message_count = convert_bez_to_mcap(bez_path, mcap_path)
            console.print(
                f"Converted to {mcap_path.name} ({message_count} messages) — open it in " "Foxglove"
            )


def _run_convert(console, args) -> int:
    """Convert already-downloaded .bez files to .mcap. Purely local."""
    _ensure_mcap_support()
    from .mcap import convert_bez_to_mcap

    inputs = [Path(name).expanduser() for name in args.files]
    missing = [str(path) for path in inputs if not path.is_file()]
    if missing:
        raise CliError(f"No such file: {', '.join(missing)}")

    output_dir = Path(args.output).expanduser() if args.output else None
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)

    for bez_path in inputs:
        mcap_path = (output_dir or bez_path.parent) / f"{bez_path.stem}.mcap"
        with console.status(f"[cyan]Converting {bez_path.name}..."):
            message_count = convert_bez_to_mcap(bez_path, mcap_path)
        console.print(f"Converted {bez_path.name} to {mcap_path} ({message_count} messages)")
    return 0


def _select_downloads(args, log_files) -> list:
    """Resolve the download selection from names/--latest/--all."""
    selectors = [bool(args.names), args.latest is not None, args.all]
    if sum(selectors) > 1:
        raise CliError("Pass only one of log names, --latest N, or --all.")
    by_name = {log.name: log for log in log_files}
    if args.all:
        return list(log_files)
    if args.latest is not None:
        if args.latest < 1:
            raise CliError("--latest must be a positive number of logs.")
        newest_first = sorted(log_files, key=lambda log: log.start_time, reverse=True)
        return newest_first[: args.latest]
    if args.names:
        missing = [name for name in args.names if name not in by_name]
        if missing:
            available = ", ".join(sorted(by_name)) or "none"
            raise CliError(
                f"No log named {', '.join(missing)} on the drone (available: {available})."
            )
        return [by_name[name] for name in args.names]
    raise CliError("Nothing selected — pass log names, --latest N, or --all.")


def _run_interactive(console, args, prompter, drone) -> int:
    """One scrollable, filterable, multi-select table of logs to download."""
    log_files = _log_rows(drone.logs, args)
    if not log_files:
        console.print(
            "No logs match the filters." if _has_filters(args) else "No logs on the drone."
        )
        return 0

    by_row = {_format_row(log): log for log in log_files}
    header = (
        f"{'NAME'.ljust(_NAME_WIDTH)}{'TIME'.ljust(_TIME_WIDTH)}{'SIZE'.ljust(_SIZE_WIDTH)}DIVE"
    )
    console.print(f"[bold]  {header}[/bold]")
    selected = prompter.checkbox(
        "Select logs to download (type to filter):", list(by_row), "--latest/--all"
    )
    if not selected:
        console.print("Nothing selected.")
        return 0
    output_dir = Path(prompter.text("Download to directory:", ".", "--output")).expanduser()
    convert_mcap = prompter.confirm("Also convert to .mcap for Foxglove?", False, "--mcap")
    _download_logs(
        console,
        [by_row[row] for row in selected],
        output_dir,
        args.timeout,
        convert_mcap=convert_mcap,
    )
    return 0


def _has_filters(args) -> bool:
    return bool(
        getattr(args, "dives_only", False)
        or getattr(args, "since", None)
        or getattr(args, "until", None)
    )


def run(args: argparse.Namespace) -> int:
    """Dispatch the logs sub-subcommand."""
    from ... import prompts, ui

    console = ui.make_console()
    action = getattr(args, "logs_command", None)

    # `convert` is purely local — no drone connection.
    if action == "convert":
        return _run_convert(console, args)

    drone = _connect(args)
    try:
        if action == "download":
            log_files = _log_rows(drone.logs, args)
            selection = _select_downloads(args, log_files)
            _download_logs(
                console,
                selection,
                Path(args.output).expanduser(),
                args.timeout,
                convert_mcap=args.mcap,
            )
            return 0

        if action is None and sys.stdin.isatty() and sys.stdout.isatty():
            try:
                return _run_interactive(console, args, prompts.QuestionaryPrompter(), drone)
            except prompts.PromptAborted:
                console.print("[yellow]Cancelled.[/yellow]")
                return 130

        # `logs list` and non-TTY bare invocation.
        log_files = _log_rows(drone.logs, args)
        if not log_files:
            console.print(
                "No logs match the filters." if _has_filters(args) else "No logs on the drone."
            )
            return 0
        _print_logs_table(console, log_files)
        return 0
    finally:
        try:
            drone.disconnect()
        except Exception:  # Never let cleanup mask the real outcome.
            logger.debug("Failed to disconnect cleanly", exc_info=True)
