"""Rich-based terminal UI helpers for the `blueye` CLI."""

from __future__ import annotations

import logging

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TransferSpeedColumn,
)
from rich.table import Table

logger = logging.getLogger(__name__)


def make_console(quiet: bool = False) -> Console:
    """Create the console all CLI output goes through.

    Args:
        quiet: Suppress everything except errors and the final result line.
    """
    return Console(quiet=quiet, highlight=False)


def model_summary_panel(info) -> Panel:
    """Render the introspected model as a summary panel.

    Args:
        info: A :class:`~blueye.sdk.cli.commands.bundle_model.introspect.ModelInfo`.
    """
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    table.add_column("Tensor")
    table.add_column("Type")
    table.add_column("Shape")
    for spec in info.inputs:
        table.add_row(f"in   {spec.name}", spec.dtype_name, spec.shape_str)
    for spec in info.outputs:
        table.add_row(f"out  {spec.name}", spec.dtype_name, spec.shape_str)
    if info.external_data_files:
        table.add_row("data", "", ", ".join(info.external_data_files))
    for key in ("description", "task", "imgsz", "stride", "date"):
        if key in info.metadata:
            table.add_row(f"meta {key}", "", info.metadata[key])
    if "names" in info.metadata:
        names = info.metadata["names"]
        preview = names if len(names) <= 60 else names[:57] + "..."
        table.add_row("meta names", "", preview)
    return Panel(table, title=f"[bold]{info.path.name}[/bold]", border_style="cyan")


def inference_panel(config) -> Panel:
    """Render the inference result and its reasoning.

    Args:
        config: A :class:`~blueye.sdk.cli.commands.bundle_model.heuristics.InferredConfig`.
    """
    lines = []
    if config.output_format:
        certainty = "" if config.confidence == "high" else " [yellow](unconfirmed)[/yellow]"
        lines.append(f"[bold]Format:[/bold] {config.output_format}{certainty}")
    else:
        lines.append("[bold]Format:[/bold] [yellow]could not be inferred[/yellow]")
    if config.num_classes is not None:
        lines.append(f"[bold]Classes:[/bold] {config.num_classes}")
    if config.input_width and config.input_height:
        lines.append(f"[bold]Input:[/bold] {config.input_width}x{config.input_height}")
    if config.kind == "sot":
        lines.append(
            f"[bold]Template/search:[/bold] {config.template_size}px / {config.search_size}px"
        )
    for note in config.notes:
        style = "yellow" if note.startswith("warning") else "dim"
        lines.append(f"[{style}]- {note}[/{style}]")
    return Panel("\n".join(lines), title="[bold]Inferred configuration[/bold]", border_style="cyan")


def meta_preview(meta: dict) -> JSON:
    """Render the generated model_meta.json with syntax highlighting."""
    import json

    return JSON(json.dumps(meta, indent=2, ensure_ascii=False))


def make_progress(console: Console) -> Progress:
    """Create the byte-level progress bar used while writing the bundle."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        console=console,
    )
