from pathlib import Path

import onnx
import onnx.helper
import pytest

from blueye.sdk.cli.commands.bundle_model.introspect import (
    FLOAT16,
    FLOAT32,
    IntrospectionError,
    check_model,
    load_model_info,
)


def make_model(
    tmp_path: Path,
    inputs=(("images", onnx.TensorProto.FLOAT, (1, 3, 640, 640)),),
    outputs=(("output0", onnx.TensorProto.FLOAT, (1, 84, 8400)),),
    metadata: dict | None = None,
    filename: str = "model.onnx",
) -> Path:
    """Write a tiny structurally-valid ONNX file (Identity chain, no weights)."""
    graph_inputs = [
        onnx.helper.make_tensor_value_info(name, dtype, list(dims)) for name, dtype, dims in inputs
    ]
    graph_outputs = [
        onnx.helper.make_tensor_value_info(name, dtype, list(dims)) for name, dtype, dims in outputs
    ]
    # One Identity node per output keeps the graph checkable without real compute.
    nodes = [
        onnx.helper.make_node("Identity", [graph_inputs[0].name], [out.name])
        for out in graph_outputs
    ]
    graph = onnx.helper.make_graph(nodes, "test_graph", graph_inputs, graph_outputs)
    model = onnx.helper.make_model(graph, producer_name="blueye-sdk-tests")
    if metadata:
        onnx.helper.set_model_props(model, metadata)
    path = tmp_path / filename
    onnx.save(model, str(path))
    return path


def test_shapes_and_dtypes_extracted(tmp_path):
    path = make_model(tmp_path)
    info = load_model_info(path)
    assert [spec.name for spec in info.inputs] == ["images"]
    assert info.inputs[0].dtype == FLOAT32
    assert info.inputs[0].dims == (1, 3, 640, 640)
    assert info.outputs[0].dims == (1, 84, 8400)
    assert info.op_histogram == {"Identity": 1}


def test_dim_param_becomes_str(tmp_path):
    path = make_model(
        tmp_path, inputs=(("images", onnx.TensorProto.FLOAT, ("batch", 3, 640, 640)),)
    )
    info = load_model_info(path)
    assert info.inputs[0].dims[0] == "batch"


def test_fp16_input_detected(tmp_path):
    path = make_model(tmp_path, inputs=(("images", onnx.TensorProto.FLOAT16, (1, 3, 640, 640)),))
    info = load_model_info(path)
    assert info.inputs[0].dtype == FLOAT16


def test_metadata_props_round_trip(tmp_path):
    path = make_model(tmp_path, metadata={"names": "{0: 'fish'}", "task": "detect"})
    info = load_model_info(path)
    assert info.metadata["names"] == "{0: 'fish'}"
    assert info.metadata["task"] == "detect"


def test_initializer_not_reported_as_input(tmp_path):
    weight = onnx.helper.make_tensor("weight", onnx.TensorProto.FLOAT, (1,), [1.0])
    images = onnx.helper.make_tensor_value_info("images", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    out = onnx.helper.make_tensor_value_info("out", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    node = onnx.helper.make_node("Mul", ["images", "weight"], ["out"])
    graph = onnx.helper.make_graph([node], "g", [images], [out])
    # Also list the initializer as a graph input (legacy exporter style).
    graph.input.append(onnx.helper.make_tensor_value_info("weight", onnx.TensorProto.FLOAT, [1]))
    graph.initializer.append(weight)
    path = tmp_path / "model.onnx"
    onnx.save(onnx.helper.make_model(graph), str(path))

    info = load_model_info(path)
    assert [spec.name for spec in info.inputs if spec.name == "weight"] == []


def test_external_data_locations_collected(tmp_path):
    weight = onnx.helper.make_tensor("weight", onnx.TensorProto.FLOAT, (1,), [1.0])
    weight.data_location = onnx.TensorProto.EXTERNAL
    del weight.float_data[:]
    entry = weight.external_data.add()
    entry.key = "location"
    entry.value = "model.onnx_data"
    images = onnx.helper.make_tensor_value_info("images", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    out = onnx.helper.make_tensor_value_info("out", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    node = onnx.helper.make_node("Mul", ["images", "weight"], ["out"])
    graph = onnx.helper.make_graph([node], "g", [images], [out], initializer=[weight])
    path = tmp_path / "model.onnx"
    onnx.save(onnx.helper.make_model(graph), str(path))

    info = load_model_info(path)
    assert info.external_data_files == ("model.onnx_data",)


def test_missing_file_raises(tmp_path):
    with pytest.raises(IntrospectionError, match="No such file"):
        load_model_info(tmp_path / "nope.onnx")


def test_garbage_file_raises(tmp_path):
    path = tmp_path / "junk.onnx"
    path.write_bytes(b"this is not protobuf")
    with pytest.raises(IntrospectionError, match="Not a valid ONNX model"):
        load_model_info(path)


def test_check_model_passes_on_valid_model(tmp_path):
    path = make_model(tmp_path)
    assert check_model(path) is None


def test_check_model_reports_broken_model(tmp_path):
    # An Identity node referencing a missing input fails the checker.
    images = onnx.helper.make_tensor_value_info("images", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    out = onnx.helper.make_tensor_value_info("out", onnx.TensorProto.FLOAT, [1, 3, 8, 8])
    node = onnx.helper.make_node("Identity", ["does_not_exist"], ["out"])
    graph = onnx.helper.make_graph([node], "g", [images], [out])
    path = tmp_path / "model.onnx"
    onnx.save(onnx.helper.make_model(graph), str(path))
    assert check_model(path) is not None
