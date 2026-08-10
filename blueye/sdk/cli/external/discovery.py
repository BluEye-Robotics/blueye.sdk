"""Tools-directory resolution and third-party tool discovery."""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .metadata import MetadataError, ToolMetadata, parse_tool_metadata

logger = logging.getLogger(__name__)

#: Environment variable overriding the tools directory.
TOOLS_DIR_ENV = "BLUEYE_CLI_TOOLS_DIR"


def tools_dir() -> Path:
    """Resolve the third-party tools directory.

    Precedence: the :data:`TOOLS_DIR_ENV` environment variable, then the platform's
    conventional per-user data location. The directory is not created here — only
    ``blueye tools install`` creates it.
    """
    override = os.environ.get(TOOLS_DIR_ENV)
    if override:
        return Path(override).expanduser()
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform.startswith("win"):
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "blueye" / "cli-tools"


def tools_dir_source() -> str:
    """Describe where the resolved tools directory came from (for display)."""
    if os.environ.get(TOOLS_DIR_ENV):
        return f"from {TOOLS_DIR_ENV}"
    return "platform default"


@dataclass(frozen=True)
class DiscoveredTool:
    """One script found in the tools directory.

    Attributes:
        path: The script file.
        metadata: The parsed metadata, or None when parsing failed.
        error: The parse-failure reason when metadata is None.
        shadowed_by: Set when the tool's name is unusable: "built-in command" or the
            file name of an earlier tool that claimed the same name.
    """

    path: Path
    metadata: ToolMetadata | None = None
    error: str | None = None
    shadowed_by: str | None = None


def scan_tools_dir(builtin_names: frozenset[str] = frozenset()) -> list[DiscoveredTool]:
    """Scan the tools directory and parse every candidate script's metadata.

    Returns every ``*.py`` file (non-recursive, sorted by file name) as a
    DiscoveredTool, including invalid and shadowed entries — `blueye tools list` shows
    them all. Never raises for a missing or empty directory.

    Args:
        builtin_names: First-party command names; tools with a colliding name are
            marked shadowed (built-ins always win).
    """
    directory = tools_dir()
    if not directory.is_dir():
        return []

    tools: list[DiscoveredTool] = []
    claimed: dict[str, str] = {}
    for path in sorted(directory.glob("*.py")):
        if not path.is_file():
            continue
        try:
            parsed = parse_tool_metadata(path.read_text(encoding="utf-8"))
        except (MetadataError, OSError, UnicodeDecodeError) as error:
            logger.debug("Skipping tool %s: %s", path, error)
            tools.append(DiscoveredTool(path=path, error=str(error)))
            continue

        shadowed_by = None
        if parsed.name in builtin_names:
            shadowed_by = "built-in command"
        elif parsed.name in claimed:
            shadowed_by = claimed[parsed.name]
        else:
            claimed[parsed.name] = path.name
        tools.append(DiscoveredTool(path=path, metadata=parsed, shadowed_by=shadowed_by))
    return tools


def discover_tools(builtin_names: frozenset[str] = frozenset()) -> dict[str, DiscoveredTool]:
    """Return the runnable tools, keyed by name (valid metadata, not shadowed)."""
    return {
        tool.metadata.name: tool
        for tool in scan_tools_dir(builtin_names)
        if tool.metadata is not None and tool.shadowed_by is None
    }


def format_tools_epilog(tools: dict[str, DiscoveredTool]) -> str | None:
    """Build the `blueye --help` section listing discovered tools (None when empty)."""
    if not tools:
        return None
    width = max(len(name) for name in tools)
    lines = [f"external tools (from {tools_dir()}):"]
    for name in sorted(tools):
        lines.append(f"  {name.ljust(width)}  {tools[name].metadata.description}")
    lines.append("")
    lines.append("Run `blueye tools --help` to manage external tools.")
    return "\n".join(lines)
