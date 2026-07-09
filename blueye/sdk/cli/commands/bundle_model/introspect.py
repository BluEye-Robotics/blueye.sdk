"""ONNX model introspection for the `blueye bundle-model` CLI.

This is the only CLI module that imports the `onnx` package. It is imported lazily by
the subcommand, after the dependency gate in `main` has verified the `[cli]` extra is
installed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import onnx

logger = logging.getLogger(__name__)

#: onnx.TensorProto element types, mirrored so downstream modules need no onnx import.
FLOAT32 = int(onnx.TensorProto.FLOAT)
FLOAT16 = int(onnx.TensorProto.FLOAT16)

_ELEMENT_TYPE_NAMES = {
    int(value): name for name, value in onnx.TensorProto.DataType.items()  # type: ignore[attr-defined]
}


class IntrospectionError(Exception):
    """The file could not be read or is not a valid ONNX model."""


@dataclass(frozen=True)
class TensorSpec:
    """Shape and type of one graph input or output.

    Attributes:
        name: Tensor name in the graph.
        dtype: onnx.TensorProto element type as a plain int (see FLOAT32/FLOAT16).
        dims: One entry per dimension: a fixed int, a symbolic name (str, e.g. "batch"),
            or None when the dimension is completely unknown.
    """

    name: str
    dtype: int
    dims: tuple[int | str | None, ...]

    @property
    def dtype_name(self) -> str:
        """Human-readable element type name (e.g. "FLOAT", "FLOAT16")."""
        return _ELEMENT_TYPE_NAMES.get(self.dtype, f"type#{self.dtype}")

    @property
    def shape_str(self) -> str:
        """Shape rendered like ``[1, 3, 640, 640]`` with ``?`` for unknown dims."""
        rendered = ", ".join("?" if d is None else str(d) for d in self.dims)
        return f"[{rendered}]"


@dataclass(frozen=True)
class ModelInfo:
    """Everything the bundler needs to know about an ONNX model.

    Attributes:
        path: Path to the .onnx file.
        inputs: Graph inputs (initializers excluded).
        outputs: Graph outputs.
        metadata: The model's metadata_props as a plain dict (Ultralytics exports embed
            "names", "imgsz", "task", "stride", ... here).
        external_data_files: Unique file names referenced by tensors stored as external
            data. These files must live next to the .onnx and travel with it.
        op_histogram: Node op_type -> count over the whole graph (used for the DLA
            fitness assessment).
    """

    path: Path
    inputs: tuple[TensorSpec, ...] = ()
    outputs: tuple[TensorSpec, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)
    external_data_files: tuple[str, ...] = ()
    op_histogram: dict[str, int] = field(default_factory=dict)


def _tensor_spec(value_info: onnx.ValueInfoProto) -> TensorSpec:
    """Convert a graph input/output ValueInfoProto into a TensorSpec."""
    tensor_type = value_info.type.tensor_type
    dims: list[int | str | None] = []
    for dim in tensor_type.shape.dim:
        if dim.HasField("dim_value"):
            dims.append(int(dim.dim_value))
        elif dim.HasField("dim_param") and dim.dim_param:
            dims.append(dim.dim_param)
        else:
            dims.append(None)
    return TensorSpec(name=value_info.name, dtype=int(tensor_type.elem_type), dims=tuple(dims))


def _iter_tensors(graph: onnx.GraphProto):
    """Yield every TensorProto in the graph: initializers and tensor-valued node
    attributes, recursing into subgraphs (If/Loop bodies)."""
    yield from graph.initializer
    for node in graph.node:
        for attribute in node.attribute:
            if attribute.HasField("t"):
                yield attribute.t
            yield from attribute.tensors
            if attribute.HasField("g"):
                yield from _iter_tensors(attribute.g)
            for subgraph in attribute.graphs:
                yield from _iter_tensors(subgraph)


def _external_data_files(model: onnx.ModelProto) -> tuple[str, ...]:
    """Collect the unique external-data file locations referenced by the model."""
    locations: list[str] = []
    for tensor in _iter_tensors(model.graph):
        if tensor.data_location == onnx.TensorProto.EXTERNAL:
            for entry in tensor.external_data:
                if entry.key == "location" and entry.value and entry.value not in locations:
                    locations.append(entry.value)
    return tuple(locations)


def load_model_info(path: Path) -> ModelInfo:
    """Load an ONNX file and extract the information the bundler needs.

    External tensor data is not loaded into memory (the file may be gigabytes); only
    the referenced file names are recorded.

    Args:
        path: Path to the .onnx file.

    Returns:
        The extracted ModelInfo.

    Raises:
        IntrospectionError: If the file does not exist or is not a parseable ONNX model.
    """
    if not path.is_file():
        raise IntrospectionError(f"No such file: {path}")
    try:
        model = onnx.load(str(path), load_external_data=False)
    except Exception as error:  # onnx raises DecodeError and various ValueErrors.
        raise IntrospectionError(f"Not a valid ONNX model: {path} ({error})") from error

    initializer_names = {initializer.name for initializer in model.graph.initializer}
    inputs = tuple(
        _tensor_spec(value_info)
        for value_info in model.graph.input
        if value_info.name not in initializer_names
    )
    outputs = tuple(_tensor_spec(value_info) for value_info in model.graph.output)

    metadata = {prop.key: prop.value for prop in model.metadata_props}

    op_histogram: dict[str, int] = {}
    for node in model.graph.node:
        op_histogram[node.op_type] = op_histogram.get(node.op_type, 0) + 1

    return ModelInfo(
        path=path,
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
        external_data_files=_external_data_files(model),
        op_histogram=op_histogram,
    )


def check_model(path: Path) -> str | None:
    """Run the strict onnx checker on the model file.

    Args:
        path: Path to the .onnx file. The path form is used so external data is found.

    Returns:
        None when the model passes, otherwise the checker's error message. Some
        perfectly deployable models fail strict checking, so the caller decides
        whether this is fatal.
    """
    try:
        onnx.checker.check_model(str(path))
    except Exception as error:
        return str(error)
    return None
