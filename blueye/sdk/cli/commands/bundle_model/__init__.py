"""The `blueye bundle-model` command: bundle an ONNX model into a BlueyeCV package."""

from __future__ import annotations

from .. import CommandSpec
from .command import add_parser, run

COMMAND = CommandSpec(
    name="bundle-model",
    help="Bundle an ONNX model into a BlueyeCV model-package zip",
    requires=("onnx",),  # rich/questionary are core SDK dependencies.
    add_parser=add_parser,
    run=run,
)
