"""Optional-dependency detection and install guidance for the `blueye` CLI.

This module must only import from the standard library: it runs precisely when the
optional `[cli]` extra (onnx, rich, questionary) is not installed, and its job is to
tell the user how to install it on their platform instead of failing with an
ImportError.
"""

from __future__ import annotations

import importlib.util
import logging
import shutil
import sys
from typing import Iterable

logger = logging.getLogger(__name__)

#: Newest CPython minor version the `onnx` project publishes prebuilt wheels for. Kept
#: conservative; only used to print a hint, never to block.
_NEWEST_PYTHON_WITH_ONNX_WHEELS = (3, 13)


def missing(names: Iterable[str]) -> list[str]:
    """Return the import names in `names` with no importable module.

    Used by `main` to gate each command's declared optional dependencies (its
    CommandSpec.requires) before running it. All currently gateable dependencies ship
    in the `[cli]` extra; if a future command needs a different extra, the guidance
    below needs a name-to-extra map.
    """
    return [name for name in names if importlib.util.find_spec(name) is None]


def _install_command() -> str:
    """Return the install command best matching the user's environment."""
    package_spec = "blueye.sdk[cli]"
    on_windows = sys.platform.startswith("win")
    if shutil.which("uv") is not None:
        return f'uv pip install "{package_spec}"'
    if on_windows:
        # cmd.exe needs no quotes; PowerShell treats brackets specially, so single quotes
        # are the safe recommendation.
        return f"python -m pip install '{package_spec}'"
    return f'python -m pip install "{package_spec}"'


def print_install_guidance(missing: list[str]) -> None:
    """Print human-friendly guidance for installing the missing CLI dependencies.

    Uses plain print() on purpose: rich may itself be one of the missing packages.

    Args:
        missing: The import names reported by :func:`missing_cli_deps`.
    """
    print()
    print("The `blueye` CLI needs a few extra packages that are not installed:")
    print()
    for name in missing:
        print(f"  - {name}")
    print()
    print("Install them with the SDK's [cli] extra:")
    print()
    print(f"    {_install_command()}")
    print()
    if sys.platform == "darwin":
        # zsh (the macOS default shell) expands square brackets, hence the quotes.
        print('(Keep the quotes around "blueye.sdk[cli]" — zsh expands square brackets.)')
    elif sys.platform.startswith("win"):
        print("(In PowerShell, use single quotes: 'blueye.sdk[cli]'. In cmd.exe no quotes")
        print("are needed.)")
    else:
        print('(Keep the quotes around "blueye.sdk[cli]" if your shell expands brackets.)')
    if "onnx" in missing and sys.version_info[:2] > _NEWEST_PYTHON_WITH_ONNX_WHEELS:
        newest = ".".join(str(v) for v in _NEWEST_PYTHON_WITH_ONNX_WHEELS)
        running = ".".join(str(v) for v in sys.version_info[:2])
        print()
        print(
            f"Note: you are running Python {running}; the onnx package may not publish"
            f" prebuilt wheels for it yet. If the install fails while building onnx from"
            f" source, use Python 3.10-{newest} instead."
        )
    print()
