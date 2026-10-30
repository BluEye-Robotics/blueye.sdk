"""PEP 723 inline-metadata parsing for third-party `blueye` tools.

A tool script declares itself with the standard PEP 723 block, extended with a
``[tool.blueye]`` table::

    # /// script
    # requires-python = ">=3.10"
    # dependencies = ["pandas"]
    #
    # [tool.blueye]
    # name = "export-logs"
    # description = "Export dive logs to CSV"
    # min-sdk-version = "2.7.0"
    # ///

TOML parsing is tiered: :mod:`tomllib` (Python 3.11+), then :mod:`tomli` when
installed (shipped in the ``[cli]`` extra for Python 3.10), then a minimal regex
fallback so a stdlib-only Python 3.10 environment can still discover tools. The
fallback only understands double-quoted string values inside ``[tool.blueye]`` and
double-quoted strings in the ``dependencies`` array (anything else needs tomli) —
enough for the keys the CLI reads.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

#: The reference regex from PEP 723 for locating inline metadata blocks.
_PEP723_BLOCK = re.compile(
    r"(?m)^# /// (?P<type>[a-zA-Z0-9-]+)$\s(?P<content>(^#(| .*)$\s)*)^# ///$"
)

#: Fallback extraction of the [tool.blueye] section body (up to the next section).
_TOOL_SECTION = re.compile(r"(?ms)^\[tool\.blueye\]\s*$(?P<body>.*?)(?=^\[|\Z)")

#: Fallback extraction of simple `key = "value"` pairs.
_STRING_KEY = re.compile(r'(?m)^([A-Za-z0-9_-]+)\s*=\s*"([^"]*)"\s*$')

#: Fallback extraction of the top-level PEP 723 `dependencies` array.
_DEPS_ARRAY = re.compile(r"(?ms)^dependencies\s*=\s*\[(?P<items>.*?)\]")

#: Fallback extraction of the quoted strings inside that array.
_QUOTED = re.compile(r'"([^"]*)"')

#: Tool names must be usable as `blueye <name>`: lowercase, digits, hyphens, starting
#: with a letter, at most 32 characters.
NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]{0,31}$")


class MetadataError(Exception):
    """The script's inline metadata is missing or invalid; the message says why."""


@dataclass(frozen=True)
class ToolMetadata:
    """The metadata the CLI reads from a tool script.

    Attributes:
        name: The subcommand name the tool is invoked as (``blueye <name>``).
        description: One-line description shown in listings and ``blueye --help``.
        min_sdk_version: Optional minimum blueye.sdk version; mismatches warn at
            dispatch time but never block execution.
        dependencies: The PEP 723 `dependencies` requirement strings. Execution asks
            uv (when available) to layer them on top of the CLI's environment.
        parsed_with_fallback: True when the regex fallback (not a real TOML parser)
            produced this metadata.
    """

    name: str
    description: str
    min_sdk_version: str | None = None
    dependencies: tuple[str, ...] = ()
    parsed_with_fallback: bool = False

    @property
    def has_dependencies(self) -> bool:
        """True when the script declares at least one dependency."""
        return bool(self.dependencies)


def _load_toml() -> object | None:
    """Return a TOML parser module (tomllib or tomli), or None when unavailable."""
    try:
        import tomllib

        return tomllib
    except ModuleNotFoundError:
        try:
            import tomli

            return tomli
        except ModuleNotFoundError:
            return None


def extract_script_block(source: str) -> str | None:
    """Extract the un-commented TOML text of the PEP 723 ``script`` block.

    Args:
        source: The tool script's full source text.

    Returns:
        The TOML text, or None when no ``script`` block is present.

    Raises:
        MetadataError: When more than one ``script`` block exists (invalid per
            PEP 723).
    """
    blocks = [match for match in _PEP723_BLOCK.finditer(source) if match.group("type") == "script"]
    if not blocks:
        return None
    if len(blocks) > 1:
        raise MetadataError("multiple '# /// script' blocks (PEP 723 allows exactly one)")
    content = blocks[0].group("content")
    lines = []
    for line in content.splitlines():
        lines.append(line[2:] if line.startswith("# ") else line[1:])
    return "\n".join(lines) + "\n"


def _parse_with_toml(toml_module, block: str) -> dict | None:
    """Parse the block with a real TOML parser; None on syntax errors."""
    try:
        return toml_module.loads(block)
    except Exception as error:
        raise MetadataError(f"invalid TOML in the script block: {error}") from error


def _parse_with_fallback(block: str) -> tuple[dict, tuple[str, ...]]:
    """Extract [tool.blueye] string keys and the dependencies array via regex."""
    section = _TOOL_SECTION.search(block)
    table = dict(_STRING_KEY.findall(section.group("body"))) if section else {}
    array = _DEPS_ARRAY.search(block)
    dependencies = tuple(_QUOTED.findall(array.group("items"))) if array else ()
    return table, dependencies


def parse_tool_metadata(source: str) -> ToolMetadata:
    """Parse a tool script's source into its ToolMetadata.

    Args:
        source: The tool script's full source text.

    Returns:
        The parsed metadata.

    Raises:
        MetadataError: When the block is absent, unparseable, or missing/violating
            the required ``[tool.blueye]`` keys.
    """
    block = extract_script_block(source)
    if block is None:
        raise MetadataError("no '# /// script' metadata block found")

    toml_module = _load_toml()
    if toml_module is not None:
        data = _parse_with_toml(toml_module, block)
        table = data.get("tool", {}).get("blueye", {})
        if not isinstance(table, dict):
            table = {}
        raw_dependencies = data.get("dependencies", [])
        if not isinstance(raw_dependencies, list) or not all(
            isinstance(item, str) for item in raw_dependencies
        ):
            raise MetadataError("'dependencies' must be a list of requirement strings")
        dependencies = tuple(raw_dependencies)
        used_fallback = False
    else:
        table, dependencies = _parse_with_fallback(block)
        used_fallback = True

    if not table:
        raise MetadataError("no [tool.blueye] table in the script block")
    name = table.get("name")
    description = table.get("description")
    if not name or not isinstance(name, str):
        raise MetadataError("[tool.blueye] is missing the required 'name' key")
    if not NAME_PATTERN.fullmatch(name):
        raise MetadataError(
            f"tool name '{name}' is invalid (lowercase letters, digits, and hyphens; "
            "must start with a letter; at most 32 characters)"
        )
    if not description or not isinstance(description, str):
        raise MetadataError("[tool.blueye] is missing the required 'description' key")

    min_sdk_version = table.get("min-sdk-version")
    if min_sdk_version is not None and not isinstance(min_sdk_version, str):
        raise MetadataError("[tool.blueye] 'min-sdk-version' must be a string")

    return ToolMetadata(
        name=name,
        description=description,
        min_sdk_version=min_sdk_version,
        dependencies=dependencies,
        parsed_with_fallback=used_fallback,
    )
