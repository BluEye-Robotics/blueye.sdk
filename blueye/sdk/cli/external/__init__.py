"""Third-party tool support for the `blueye` CLI.

Tools are single-file Python scripts carrying PEP 723 inline metadata (a
``# /// script`` comment block) extended with a ``[tool.blueye]`` table. They live in
a per-user tools directory (see :func:`blueye.sdk.cli.external.discovery.tools_dir`),
are discovered by parsing only their metadata (never executing code), and run as
subprocesses.

Everything in this package is standard-library only, so discovery works before the
optional ``[cli]`` extra is installed.
"""
