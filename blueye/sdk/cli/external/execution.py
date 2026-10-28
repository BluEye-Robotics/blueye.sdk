"""Subprocess execution of third-party tools."""

from __future__ import annotations

import logging
import shutil
import subprocess
import sys

from .discovery import DiscoveredTool

logger = logging.getLogger(__name__)


def _sdk_version() -> str | None:
    """The installed blueye.sdk version, or None when it cannot be determined."""
    try:
        from importlib.metadata import version

        return version("blueye.sdk")
    except Exception:  # pragma: no cover - depends on installation metadata
        return None


def _version_tuple(text: str) -> tuple[int, ...] | None:
    """Parse a dotted version into an int tuple; None for non-numeric parts."""
    try:
        return tuple(int(part) for part in text.split("."))
    except ValueError:
        return None


def _warn_min_sdk_version(tool: DiscoveredTool) -> None:
    """Warn (never block) when the tool requests a newer SDK than installed."""
    wanted = tool.metadata.min_sdk_version
    if not wanted:
        return
    installed = _sdk_version()
    wanted_tuple = _version_tuple(wanted)
    installed_tuple = _version_tuple(installed) if installed else None
    if wanted_tuple and installed_tuple and installed_tuple < wanted_tuple:
        print(
            f"warning: {tool.metadata.name} requests blueye.sdk >= {wanted} "
            f"(installed: {installed}); it may not work correctly.",
            file=sys.stderr,
        )


def run_tool(tool: DiscoveredTool, args: list[str]) -> int:
    """Run a discovered tool as a subprocess and return its exit code.

    The tool always runs on the CLI's own interpreter, so it can import the same
    ``blueye.sdk`` the CLI runs on (and anything else installed next to it). When the
    script declares PEP 723 ``dependencies`` and uv is available, uv layers those
    packages on top of this environment (``uv run --with <requirement>`` for each);
    they live in uv's cache and nothing is installed into the CLI's environment. The
    requirements are passed one by one rather than via ``--with-requirements
    <script>``, which only reads PEP 723 scripts from uv 0.9 on. Without uv, the
    declared dependencies must already be importable here.

    Args:
        tool: The tool to run (must have valid metadata).
        args: Arguments passed through to the script verbatim.
    """
    _warn_min_sdk_version(tool)

    if tool.metadata.has_dependencies and shutil.which("uv") is not None:
        with_options = [
            option
            for requirement in tool.metadata.dependencies
            for option in ("--with", requirement)
        ]
        command = [
            "uv",
            "run",
            "--no-project",
            "--python",
            sys.executable,
            *with_options,
            "python",
            str(tool.path),
            *args,
        ]
    else:
        if tool.metadata.has_dependencies:
            logger.debug(
                "Tool %s declares dependencies but uv is not available; running with "
                "the current interpreter.",
                tool.metadata.name,
            )
        command = [sys.executable, str(tool.path), *args]

    logger.debug("Running external tool: %s", command)
    return subprocess.run(command, check=False).returncode
