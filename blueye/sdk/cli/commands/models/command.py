"""Implementation of the `blueye models` subcommands.

Thin CLI wrappers over :class:`blueye.sdk.cv_models.CvModels`, plus an interactive
management loop when invoked bare on a terminal. Model identifiers are the package
directory slugs shown by `blueye models list`. The `enabled` state is the autolaunch
configuration — the drone's API does not expose a live "running" status.

Argument definitions are stdlib-only; rich/questionary/blueye.sdk imports happen
inside `run` (after the dependency gate).
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from ...errors import CliError
from .._common import drone_options_parser, friendly_errors

logger = logging.getLogger(__name__)

_DEVICES = ("cuda", "tensorrt", "tensorrt-dla0", "tensorrt-dla1")
_HZ_CHOICES = (0, 5, 10, 15)


def add_parser(subparsers) -> None:
    """Register the ``models`` subcommand and its sub-subcommands."""
    common = drone_options_parser(timeout_default=5.0)

    parser = subparsers.add_parser(
        "models",
        parents=[common],
        help="Manage the CV model packages installed on the drone",
        description=(
            "List, configure, and manage the CV model packages on the drone. Run without "
            "an action on a terminal for an interactive management session. Model names "
            "are the directory slugs shown by `blueye models list`; the enabled state is "
            "the autolaunch configuration."
        ),
    )
    actions = parser.add_subparsers(dest="models_command", metavar="ACTION")

    actions.add_parser("list", parents=[common], help="List the models on the drone")

    enable = actions.add_parser("enable", parents=[common], help="Enable a model's autolaunch")
    enable.add_argument("name", help="The model's directory slug")
    disable = actions.add_parser("disable", parents=[common], help="Disable a model's autolaunch")
    disable.add_argument("name", help="The model's directory slug")

    set_device = actions.add_parser(
        "set-device", parents=[common], help="Set the execution provider a model runs on"
    )
    set_device.add_argument("name", help="The model's directory slug")
    set_device.add_argument("device", choices=list(_DEVICES))

    set_hz = actions.add_parser(
        "set-hz", parents=[common], help="Set a model's maximum inference rate"
    )
    set_hz.add_argument("name", help="The model's directory slug")
    set_hz.add_argument(
        "hz", type=int, choices=list(_HZ_CHOICES), help="Rate in Hz (0 = unlimited)"
    )

    warmup = actions.add_parser(
        "warmup",
        parents=[common],
        help="Pre-build a model's inference engine (TensorRT builds take minutes)",
    )
    warmup.add_argument("name", help="The model's directory slug")

    delete = actions.add_parser("delete", parents=[common], help="Delete a model from the drone")
    delete.add_argument("name", help="The model's directory slug")
    delete.add_argument("--force", action="store_true", help="Do not ask for confirmation")

    upload = actions.add_parser(
        "upload", parents=[common], help="Upload a model package zip to the drone"
    )
    upload.add_argument("package", help="Path to the package zip")

    download = actions.add_parser(
        "download", parents=[common], help="Download a model package from the drone"
    )
    download.add_argument("name", help="The model's directory slug")
    download.add_argument("-o", "--output", help="Destination file or directory")

    actions.add_parser(
        "rescan", parents=[common], help="Ask the drone's vision pipeline to rescan the packages"
    )


def _cv_models(args):
    """Build the CvModels client for the requested drone (HTTP only, no control)."""
    from blueye.sdk import Drone

    return Drone(ip=args.drone_ip, auto_connect=False).cv_models


def _runtime_field(model, key: str, default: str = "-") -> str:
    value = model.raw.get("runtime", {}).get(key)
    return str(value) if value is not None else default


def _print_models_table(console, models) -> None:
    from rich.table import Table

    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    for column in ("NAME", "DIRECTORY", "TYPE", "FORMAT", "SIZE", "ENABLED", "DEVICE", "HZ"):
        table.add_column(column)
    for model in models:
        size_mb = model.size_bytes / (1024 * 1024)
        hz = _runtime_field(model, "hz")
        table.add_row(
            model.name,
            model.directory,
            model.type,
            model.output_format,
            f"{size_mb:.1f} MB",
            "[green]yes[/green]" if model.enabled else "[dim]no[/dim]",
            _runtime_field(model, "device"),
            "max" if hz == "0" else hz,
        )
    console.print(table)


def _run_list(console, args) -> int:
    models = friendly_errors(lambda: _cv_models(args).list(timeout=args.timeout))
    if not models:
        console.print("No CV models installed on the drone.")
        return 0
    _print_models_table(console, models)
    return 0


def _run_interactive(console, args, prompter) -> int:
    """Interactive management loop: pick a model, pick an action, repeat."""
    cv_models = _cv_models(args)
    while True:
        models = friendly_errors(lambda: cv_models.list(timeout=args.timeout))
        if not models:
            console.print("No CV models installed on the drone.")
            return 0
        _print_models_table(console, models)

        by_label = {}
        for model in models:
            state = "enabled" if model.enabled else "disabled"
            device = _runtime_field(model, "device")
            by_label[f"{model.directory} ({state}, {device})"] = model
        quit_label = "Quit"
        choice = prompter.select("Select a model:", [*by_label, quit_label], quit_label, "ACTION")
        if choice == quit_label:
            return 0
        model = by_label[choice]

        toggle = f"{'Disable' if model.enabled else 'Enable'} autolaunch"
        action = prompter.select(
            f"Action for '{model.directory}':",
            [toggle, "Set device", "Set rate", "Warm up", "Delete", "Back"],
            "Back",
            "ACTION",
        )
        if action == toggle:
            friendly_errors(
                lambda: cv_models.set_enabled(
                    model.directory, not model.enabled, timeout=args.timeout
                )
            )
        elif action == "Set device":
            device = prompter.select(
                "Execution device:", list(_DEVICES), _runtime_field(model, "device"), "ACTION"
            )
            friendly_errors(
                lambda: cv_models.set_device(model.directory, device, timeout=args.timeout)
            )
        elif action == "Set rate":
            rate = prompter.select(
                "Maximum rate:",
                [("max (0)" if hz == 0 else str(hz)) for hz in _HZ_CHOICES],
                "max (0)",
                "ACTION",
            )
            hz = 0 if rate.startswith("max") else int(rate)
            friendly_errors(lambda: cv_models.set_hz(model.directory, hz, timeout=args.timeout))
        elif action == "Warm up":
            with console.status(
                f"[cyan]Warming up '{model.directory}' (TensorRT builds can take minutes)..."
            ):
                friendly_errors(lambda: cv_models.warmup(model.directory))
        elif action == "Delete":
            if prompter.confirm(f"Delete '{model.directory}' from the drone?", False, "--force"):
                friendly_errors(lambda: cv_models.delete(model.directory, timeout=args.timeout))


def run(args: argparse.Namespace) -> int:
    """Dispatch the models sub-subcommand."""
    from ... import prompts, ui

    console = ui.make_console()
    action = getattr(args, "models_command", None)

    if action is None:
        if sys.stdin.isatty() and sys.stdout.isatty():
            try:
                return _run_interactive(console, args, prompts.QuestionaryPrompter())
            except prompts.PromptAborted:
                console.print("[yellow]Cancelled.[/yellow]")
                return 130
        return _run_list(console, args)

    if action == "list":
        return _run_list(console, args)

    cv_models = _cv_models(args)
    if action == "enable":
        friendly_errors(lambda: cv_models.set_enabled(args.name, True, timeout=args.timeout))
        console.print(f"Enabled autolaunch for '{args.name}'.")
    elif action == "disable":
        friendly_errors(lambda: cv_models.set_enabled(args.name, False, timeout=args.timeout))
        console.print(f"Disabled autolaunch for '{args.name}'.")
    elif action == "set-device":
        friendly_errors(lambda: cv_models.set_device(args.name, args.device, timeout=args.timeout))
        console.print(f"'{args.name}' now runs on {args.device}.")
    elif action == "set-hz":
        friendly_errors(lambda: cv_models.set_hz(args.name, args.hz, timeout=args.timeout))
        rate = "unlimited" if args.hz == 0 else f"{args.hz} Hz"
        console.print(f"'{args.name}' rate set to {rate}.")
    elif action == "warmup":
        with console.status(
            f"[cyan]Warming up '{args.name}' (TensorRT builds can take minutes)..."
        ):
            friendly_errors(lambda: cv_models.warmup(args.name))
        console.print(f"Warmup of '{args.name}' complete.")
    elif action == "delete":
        if not args.force:
            from ... import prompts

            interactive = sys.stdin.isatty() and sys.stdout.isatty()
            if not interactive:
                raise CliError(f"Deleting '{args.name}' requires --force when not interactive.")
            if not prompts.QuestionaryPrompter().confirm(
                f"Delete '{args.name}' from the drone?", False, "--force"
            ):
                return 1
        friendly_errors(lambda: cv_models.delete(args.name, timeout=args.timeout))
        console.print(f"Deleted '{args.name}' from the drone.")
    elif action == "upload":
        package = Path(args.package).expanduser()
        if not package.is_file():
            raise CliError(f"No such file: {package}")
        with console.status("[cyan]Uploading to the drone..."):
            model = friendly_errors(lambda: cv_models.upload(package))
        state = "enabled" if model.enabled else "disabled"
        console.print(f"Uploaded '{model.name}' as '{model.directory}' (autolaunch {state}).")
    elif action == "download":
        output = Path(args.output).expanduser() if args.output else None
        with console.status("[cyan]Downloading from the drone..."):
            path = friendly_errors(lambda: cv_models.download(args.name, output_path=output))
        console.print(f"Downloaded '{args.name}' to {path}.")
    elif action == "rescan":
        friendly_errors(lambda: cv_models.rescan(timeout=args.timeout))
        console.print("Rescan triggered.")
    return 0
