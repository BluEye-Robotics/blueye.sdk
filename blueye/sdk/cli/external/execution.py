"""Subprocess execution of third-party tools."""

from __future__ import annotations

import logging
import os
import shutil
import site
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


# Runs a script the way ``python script.py args`` does, after adding the CLI's per-user
# package folder to the end of the module search path. Arguments: user site, script, args.
# The script is compiled and executed in this module's own namespace, so it stays the
# interpreter's ``__main__`` through atexit handlers and sys.excepthook, as it would when
# run directly. ``__file__`` is absolute and ``sys.path[0]`` is the script's directory
# with symlinks resolved, which is what the interpreter does; ``sys.argv[0]`` is the path
# as given.
_USER_SITE_BOOTSTRAP = """\
import os, site, sys
__file__ = os.path.abspath(sys.argv[2])
sys.path[0] = os.path.dirname(os.path.realpath(__file__))
site.addsitedir(sys.argv[1])
sys.argv[:] = sys.argv[2:]
with open(__file__, "rb") as _source:
    _code = compile(_source.read(), __file__, "exec")
del os, site, sys, _source
exec(_code)
"""


def _user_site_to_forward() -> str | None:
    """The per-user package folder the tool needs, or None when there is nothing to add.

    uv layers the tool's packages in a virtualenv on top of the CLI's interpreter, and
    the virtualenv does not read the per-user package folder (``pip install --user``,
    the fallback on system Pythons without write access to site-packages). An SDK
    installed there would be invisible to the tool. The folder is forwarded when the
    CLI itself runs with the user site enabled, which Python turns off inside a
    virtualenv unless it was created with system site packages.

    The folder is added at the end of the search path from inside the tool's
    interpreter rather than through ``PYTHONPATH``: ``PYTHONPATH`` entries come before
    every site-packages directory, so a user-site copy of a package would shadow the
    version uv installed for the tool.
    """
    if not site.ENABLE_USER_SITE:
        return None
    user_site = site.getusersitepackages()
    if not os.path.isdir(user_site):
        return None
    return user_site


def run_tool(tool: DiscoveredTool, args: list[str]) -> int:
    """Run a discovered tool as a subprocess and return its exit code.

    The tool always runs on the CLI's own interpreter, so it can import the same
    ``blueye.sdk`` the CLI runs on (and anything else installed next to it). When the
    script declares PEP 723 ``dependencies`` and uv is available, uv layers those
    packages on top of this environment (``uv run --with <requirement>`` for each);
    they live in uv's cache and nothing is installed into the CLI's environment. The
    requirements are passed one by one rather than via ``--with-requirements
    <script>``, which only reads PEP 723 scripts from uv 0.9 on. An SDK installed in
    the per-user package folder is added to the tool's search path after uv's
    packages, see ``_user_site_to_forward``. Without uv, the declared dependencies
    must already be importable here.

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
        user_site = _user_site_to_forward()
        if user_site is None:
            script = [str(tool.path)]
        else:
            script = ["-c", _USER_SITE_BOOTSTRAP, user_site, str(tool.path)]
        command = [
            "uv",
            "run",
            "--no-project",
            "--python",
            sys.executable,
            *with_options,
            "python",
            *script,
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
