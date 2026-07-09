# Extending the blueye CLI

The `blueye` command is built to grow. There are two ways to add commands:

- **Built-in commands** live in the SDK itself, under `blueye/sdk/cli/commands/`, and
  ship with every release — this is how `bundle-model` and `tools` are implemented.
- **Third-party tools** are single-file Python scripts that anyone can drop into a
  per-user tools directory. The CLI discovers them automatically, lists them in
  `blueye --help`, and runs them as `blueye <tool-name> ...` — no SDK changes needed.

## Writing a third-party tool

A tool is a normal Python script carrying [PEP 723](https://peps.python.org/pep-0723/)
inline metadata, extended with a `[tool.blueye]` table:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["pandas"]
#
# [tool.blueye]
# name = "export-logs"
# description = "Export dive logs to CSV"
# min-sdk-version = "2.7.0"
# ///
import sys

import pandas as pd


def main() -> int:
    print(f"exporting with args: {sys.argv[1:]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

The `[tool.blueye]` keys:

| Key               | Required | Meaning                                                        |
| ----------------- | -------- | -------------------------------------------------------------- |
| `name`            | yes      | The subcommand name (`blueye export-logs`). Lowercase letters, digits, and hyphens; must start with a letter; at most 32 characters. |
| `description`     | yes      | One line shown in `blueye --help` and `blueye tools list`.     |
| `min-sdk-version` | no       | Minimum blueye.sdk version; a mismatch prints a warning but never blocks. |

Arguments after the tool name are passed to the script verbatim, and its exit code
becomes the CLI's exit code. Invocation is strictly `blueye <tool-name> args...`.

**Dependencies**: when the script declares PEP 723 `dependencies` and
[uv](https://docs.astral.sh/uv/) is installed, the CLI runs it with `uv run`, giving
the script an isolated environment with those dependencies — your tool can use pandas
without pandas ever being installed next to the SDK. Without uv, the script runs with
the current interpreter and must find its dependencies there.

## Installing and managing tools

```shell
blueye tools validate my_script.py   # check the metadata before installing
blueye tools install my_script.py    # copy it into the tools directory
blueye tools list                    # built-ins + installed tools
blueye tools uninstall export-logs
blueye tools dir                     # print the resolved tools directory
```

Discovery scans the tools directory on every invocation and parses **only the
metadata block — tool code is never executed during discovery** or listing.

The directory is resolved from the `BLUEYE_CLI_TOOLS_DIR` environment variable when
set, otherwise from the platform default:

| Platform | Default tools directory                              |
| -------- | ---------------------------------------------------- |
| macOS    | `~/Library/Application Support/blueye/cli-tools`     |
| Linux    | `$XDG_DATA_HOME/blueye/cli-tools` (or `~/.local/share/blueye/cli-tools`) |
| Windows  | `%APPDATA%\blueye\cli-tools`                         |

Name collisions always resolve in favor of built-in commands; `blueye tools list`
shows shadowed or invalid tools with the reason.

## Adding a built-in command (SDK contributors)

Each built-in command is a self-contained package under `blueye/sdk/cli/commands/`
exposing a `COMMAND` spec:

```python
# blueye/sdk/cli/commands/my_command/__init__.py
from .. import CommandSpec
from .command import add_parser, run

COMMAND = CommandSpec(
    name="my-command",
    help="One line shown in `blueye --help`",
    requires=("rich",),  # optional deps gated before run(); () if stdlib-only
    add_parser=add_parser,  # argparse-only argument definitions
    run=run,  # returns the exit code; heavy imports go inside
)
```

Register it in `all_commands()` in `blueye/sdk/cli/commands/__init__.py` — that is the
only central change. The invariants:

- The command package must be importable with **zero optional extras** installed
  (`blueye --help` runs before the `[cli]` extra exists). Import onnx/rich/questionary
  inside `run`, never at module level.
- Declare optional imports in `requires`; the CLI prints install guidance and exits
  with code 2 when they are missing.
- Raise `blueye.sdk.cli.errors.CliError` for user-facing failures — it is printed as a
  clean message, never a traceback.

## Future work: pip-installable plugins

A third route is planned but not yet implemented: packages registering a
`CommandSpec` under a `blueye.cli` [entry-point group](https://packaging.python.org/en/latest/specifications/entry-points/),
so `pip install blueye-tool-x` would add a subcommand. The `CommandSpec` contract
above is designed to be that plugin interface unchanged.
