"""Model-type inference for the `blueye bundle-model` CLI.

Pure functions over :class:`~blueye.sdk.cli.introspect.ModelInfo`-shaped data: no
onnx import, no I/O, no terminal — everything here is unit-testable with hand-built
dataclasses. The rules mirror what the BlueyeCV output decoders expect (see
BlueyeCV/docs/model-meta-spec.md).
"""

from __future__ import annotations

import ast
import logging
from dataclasses import dataclass, field
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from .introspect import ModelInfo, TensorSpec

logger = logging.getLogger(__name__)

#: onnx.TensorProto element types (mirrored to avoid an onnx import).
_FLOAT32 = 1
_FLOAT16 = 10

#: All output formats BlueyeCV supports, in the order shown to the user.
DETECTION_FORMATS = (
    "yolov2_grid",
    "yolov5_flat",
    "yolov8_flat",
    "yolov8_seg",
    "yolo_e2e",
    "yolo_e2e_seg",
    "ssd_multi",
    "detr",
)
SOT_FORMATS = ("ostrack", "mixformerv2")
ALL_FORMATS = DETECTION_FORMATS + SOT_FORMATS

#: Number of mask coefficients / prototype channels in YOLO -seg heads.
_NUM_MASK_COEFFS = 32


class UnsupportedModelError(Exception):
    """The model is clearly not usable by BlueyeCV; the message explains why."""


@dataclass
class InferredConfig:
    """What could be derived from the model, plus how sure we are.

    Attributes:
        kind: "detection", "sot", or "unknown" (format must be chosen manually).
        output_format: The inferred model_meta output_format, or None.
        confidence: "high" when the shape/metadata evidence is unambiguous; "low" when
            the format should be confirmed with the user.
        num_classes: Class count derived from the output shape or metadata.
        input_width: Model input width in pixels (None if dynamic/unknown).
        input_height: Model input height in pixels (None if dynamic/unknown).
        grid_size: Feature-map grid size (yolov2_grid only).
        template_size: SOT template crop size (from the template input).
        search_size: SOT search crop size (from the search input).
        labels: Class labels from embedded metadata, index order preserved.
        suggested_name: Human-readable name suggestion (metadata description or None).
        notes: Human-readable reasoning, shown in the inference summary.
    """

    kind: Literal["detection", "sot", "unknown"] = "unknown"
    output_format: str | None = None
    confidence: Literal["high", "low"] = "low"
    num_classes: int | None = None
    input_width: int | None = None
    input_height: int | None = None
    grid_size: int | None = None
    template_size: int | None = None
    search_size: int | None = None
    labels: list[str] | None = None
    suggested_name: str | None = None
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DlaAssessment:
    """Whether the model is a good fit for the Jetson DLA cores, and why."""

    good_fit: bool
    reason: str


def _fixed(dim: int | str | None) -> int | None:
    """Return the dimension as an int when it is fixed, else None."""
    return dim if isinstance(dim, int) else None


def _is_image_input(spec: TensorSpec) -> bool:
    """True for a 4-D float tensor with 1 or 3 channels in NCHW or NHWC layout."""
    if len(spec.dims) != 4 or spec.dtype not in (_FLOAT32, _FLOAT16):
        return False
    channels_first = _fixed(spec.dims[1])
    channels_last = _fixed(spec.dims[3])
    return channels_first in (1, 3) or channels_last in (1, 3)


def _image_hw(spec: TensorSpec) -> tuple[int | None, int | None]:
    """Return (height, width) of an image input, handling NCHW vs NHWC."""
    if _fixed(spec.dims[1]) in (1, 3):  # NCHW
        return _fixed(spec.dims[2]), _fixed(spec.dims[3])
    return _fixed(spec.dims[1]), _fixed(spec.dims[2])  # NHWC


def parse_ultralytics_metadata(metadata: dict[str, str]) -> dict[str, object]:
    """Parse the metadata_props Ultralytics embeds in its ONNX exports.

    Args:
        metadata: The raw metadata_props key/value dict.

    Returns:
        A dict possibly containing "labels" (list[str]), "imgsz" ((height, width)),
        "task" (str), and "description" (str). Keys are absent when not parseable.
    """
    parsed: dict[str, object] = {}
    names_repr = metadata.get("names")
    if names_repr:
        try:
            names = ast.literal_eval(names_repr)
            if isinstance(names, dict):
                parsed["labels"] = [str(names[key]) for key in sorted(names)]
            elif isinstance(names, (list, tuple)):
                parsed["labels"] = [str(name) for name in names]
        except (ValueError, SyntaxError):
            logger.debug("Could not parse metadata 'names': %r", names_repr)
    imgsz_repr = metadata.get("imgsz")
    if imgsz_repr:
        try:
            imgsz = ast.literal_eval(imgsz_repr)
            if isinstance(imgsz, (list, tuple)) and len(imgsz) == 2:
                parsed["imgsz"] = (int(imgsz[0]), int(imgsz[1]))
        except (ValueError, SyntaxError):
            logger.debug("Could not parse metadata 'imgsz': %r", imgsz_repr)
    if metadata.get("task"):
        parsed["task"] = metadata["task"]
    if metadata.get("description"):
        parsed["description"] = metadata["description"]
    return parsed


def _reject_unsupported(info: ModelInfo, image_inputs: list[TensorSpec]) -> None:
    """Raise UnsupportedModelError for models BlueyeCV can clearly never run."""
    if not image_inputs:
        described = (
            ", ".join(f"{spec.name}: {spec.dtype_name} {spec.shape_str}" for spec in info.inputs)
            or "(no inputs)"
        )
        raise UnsupportedModelError(
            "The model has no image-like input tensor. BlueyeCV expects a 4-D float "
            f"tensor with 1 or 3 channels (e.g. [1, 3, 640, 640]); found: {described}."
        )
    for spec in image_inputs:
        if spec.dtype == _FLOAT16:
            raise UnsupportedModelError(
                f"Input '{spec.name}' is float16. BlueyeCV feeds float32 tensors — "
                "re-export the model with float32 inputs (e.g. half=False for "
                "Ultralytics exports). Models with fp16 weights but float32 "
                "inputs/outputs are fine."
            )
    if len(image_inputs) > 3:
        raise UnsupportedModelError(
            f"The model has {len(image_inputs)} image inputs; BlueyeCV supports "
            "detection models (1 input) and single-object trackers (2-3 inputs)."
        )
    if len(image_inputs) == 1 and len(info.outputs) == 1:
        output = info.outputs[0]
        dims = [_fixed(dim) for dim in output.dims]
        is_2d_classes = len(dims) == 2 and (dims[1] or 0) > 1
        is_4d_squeezed = len(dims) == 4 and dims[2] == 1 and dims[3] == 1 and (dims[1] or 0) > 1
        if is_2d_classes or is_4d_squeezed:
            raise UnsupportedModelError(
                f"The output shape {output.shape_str} looks like an image classifier. "
                "BlueyeCV runs object detection and single-object tracking models only."
            )


def _infer_sot(info: ModelInfo, image_inputs: list[TensorSpec], config: InferredConfig) -> None:
    """Fill in the config for a 2- or 3-image-input single-object tracker."""
    config.kind = "sot"
    by_height = sorted(image_inputs, key=lambda spec: _image_hw(spec)[0] or 0)
    template, search = by_height[0], by_height[-1]
    config.template_size = _image_hw(template)[0]
    config.search_size = _image_hw(search)[0]
    config.input_width = config.search_size
    config.input_height = config.search_size
    # OSTrack exports two inputs (template, search); MixFormerV2 exports three
    # (template, online_template, search).
    config.output_format = "ostrack" if len(image_inputs) == 2 else "mixformerv2"
    config.confidence = "low"  # Same input structure could come from other trackers.
    config.labels = ["tracked"]
    config.notes.append(
        f"{len(image_inputs)} image inputs (template {config.template_size}px / search "
        f"{config.search_size}px) -> single-object tracker, {config.output_format}-style"
    )


def _infer_detection_two_outputs(outputs: tuple[TensorSpec, ...], config: InferredConfig) -> None:
    """Handle the two-output families: YOLO segmentation heads and DETR."""
    first_dims = [_fixed(dim) for dim in outputs[0].dims]
    second_dims = [_fixed(dim) for dim in outputs[1].dims]

    # Segmentation: the second output is the [1, 32, h, w] mask prototype tensor.
    if len(second_dims) == 4 and second_dims[1] == _NUM_MASK_COEFFS:
        if len(first_dims) == 3 and (first_dims[2] or 0) == 6 + _NUM_MASK_COEFFS:
            config.kind = "detection"
            config.output_format = "yolo_e2e_seg"
            config.confidence = "high"
            config.notes.append(
                f"outputs {outputs[0].shape_str} + mask prototypes -> end-to-end "
                "segmentation (NMS in the model)"
            )
            return
        if len(first_dims) == 3 and first_dims[1] is not None:
            config.kind = "detection"
            config.output_format = "yolov8_seg"
            config.confidence = "high"
            config.num_classes = first_dims[1] - 4 - _NUM_MASK_COEFFS
            config.notes.append(
                f"outputs {outputs[0].shape_str} + mask prototypes -> YOLOv8-style "
                f"segmentation, {config.num_classes} classes"
            )
            return

    # DETR: logits [1, Q, C+1] + boxes [1, Q, 4].
    if (
        len(first_dims) == 3
        and len(second_dims) == 3
        and second_dims[2] == 4
        and (first_dims[2] or 0) > 4
        and first_dims[1] == second_dims[1]
    ):
        config.kind = "detection"
        config.output_format = "detr"
        config.confidence = "high"
        config.num_classes = (first_dims[2] or 1) - 1
        config.notes.append(
            f"logits {outputs[0].shape_str} + boxes {outputs[1].shape_str} -> DETR, "
            f"{config.num_classes} classes (+1 no-object logit)"
        )


def _infer_detection_single_output(output: TensorSpec, config: InferredConfig) -> None:
    """Handle the single-output families: e2e, v8-flat, v5-flat, and v2-grid."""
    dims = [_fixed(dim) for dim in output.dims]

    if len(dims) == 3 and dims[2] == 6:
        config.kind = "detection"
        config.output_format = "yolo_e2e"
        config.confidence = "high"
        config.notes.append(
            f"output {output.shape_str} (x1,y1,x2,y2,score,class rows) -> end-to-end "
            "YOLO (NMS in the model)"
        )
        return

    if len(dims) == 3 and dims[1] is not None and dims[2] is not None:
        rows, cols = dims[1], dims[2]
        if rows < cols and rows > 4:
            config.kind = "detection"
            config.output_format = "yolov8_flat"
            config.confidence = "high"
            config.num_classes = rows - 4
            config.notes.append(
                f"output {output.shape_str} (channels-first, 4+C rows) -> YOLOv8 flat, "
                f"{config.num_classes} classes"
            )
            return
        if cols < rows and cols > 5:
            config.kind = "detection"
            config.output_format = "yolov5_flat"
            config.confidence = "high"
            config.num_classes = cols - 5
            config.notes.append(
                f"output {output.shape_str} (rows of 5+C values) -> YOLOv5 flat, "
                f"{config.num_classes} classes"
            )
            return

    if len(dims) == 4 and dims[2] is not None and dims[2] == dims[3] and (dims[1] or 0) > 0:
        config.kind = "detection"
        config.output_format = "yolov2_grid"
        config.confidence = "low"  # anchors/classes are not derivable from the shape
        config.grid_size = dims[2]
        config.notes.append(
            f"output {output.shape_str} -> YOLOv2-style grid (grid {dims[2]}x{dims[3]}); "
            "anchors and class count come from the training config"
        )


def infer(info: ModelInfo) -> InferredConfig:
    """Infer the BlueyeCV model configuration from the ONNX graph and metadata.

    Args:
        info: The introspected model.

    Returns:
        An InferredConfig; ``kind == "unknown"`` means the format must be chosen
        manually.

    Raises:
        UnsupportedModelError: When the model clearly cannot run in BlueyeCV
            (classifier, no image input, float16 input, too many inputs).
    """
    config = InferredConfig()
    image_inputs = [spec for spec in info.inputs if _is_image_input(spec)]
    _reject_unsupported(info, image_inputs)

    # Input geometry from the (primary) image input.
    height, width = _image_hw(image_inputs[0])
    config.input_height = height
    config.input_width = width

    # Ultralytics metadata beats shape guessing where present.
    ultralytics = parse_ultralytics_metadata(info.metadata)
    if "labels" in ultralytics:
        config.labels = list(ultralytics["labels"])  # type: ignore[arg-type]
        config.notes.append(f"{len(config.labels)} labels from embedded Ultralytics metadata")
    if "imgsz" in ultralytics and (height is None or width is None):
        config.input_height, config.input_width = ultralytics["imgsz"]  # type: ignore[misc]
        config.notes.append("input size from embedded 'imgsz' metadata")
    if "description" in ultralytics:
        config.suggested_name = str(ultralytics["description"])

    if len(image_inputs) >= 2:
        _infer_sot(info, image_inputs, config)
        return config

    outputs = info.outputs
    if len(outputs) == 2:
        _infer_detection_two_outputs(outputs, config)
    elif len(outputs) == 1:
        _infer_detection_single_output(outputs[0], config)
    elif len(outputs) == 4:
        config.kind = "detection"
        config.output_format = "ssd_multi"
        config.confidence = "low"
        config.notes.append("4 outputs (boxes/classes/scores/count) -> SSD-style multi-output")

    # Cross-check the class count against embedded labels.
    if config.labels is not None and config.num_classes is None:
        config.num_classes = len(config.labels)
    if (
        config.labels is not None
        and config.num_classes is not None
        and len(config.labels) != config.num_classes
        and config.kind == "detection"
    ):
        config.notes.append(
            f"warning: {len(config.labels)} embedded labels but the output shape implies "
            f"{config.num_classes} classes"
        )

    if config.output_format is None:
        config.kind = "unknown"
        config.notes.append("output shapes did not match any known decoder format")
    return config


#: Ops that force (partial) GPU fallback or are architecture markers of transformer
#: models — both make a model a poor DLA candidate.
_DLA_UNFRIENDLY_OPS = {
    "NonMaxSuppression",
    "TopK",
    "LayerNormalization",
    "SkipLayerNormalization",
    "Einsum",
    "Attention",
    "MultiHeadAttention",
    "GridSample",
    "ScatterND",
    "RoiAlign",
}

#: Convolution-network ops the DLA executes natively.
_DLA_FRIENDLY_OPS = {
    "Conv",
    "ConvTranspose",
    "MaxPool",
    "AveragePool",
    "GlobalAveragePool",
    "Relu",
    "LeakyRelu",
    "PRelu",
    "Sigmoid",
    "Tanh",
    "BatchNormalization",
    "Add",
    "Mul",
    "Concat",
    "Resize",
    "Upsample",
}


def assess_dla_fitness(info: ModelInfo) -> DlaAssessment:
    """Judge whether the model is a good candidate for the Jetson DLA cores.

    The DLA natively executes convolution-style networks; NMS/TopK and
    attention/normalization layers fall back to the GPU, negating the benefit. This is
    a heuristic over the op histogram — TensorRT has the final word when the engine is
    built on the drone.

    Args:
        info: The introspected model.

    Returns:
        A DlaAssessment with the verdict and a one-line reason.
    """
    histogram = info.op_histogram
    unfriendly = sorted(op for op in histogram if op in _DLA_UNFRIENDLY_OPS)
    matmul_count = histogram.get("MatMul", 0) + histogram.get("Gemm", 0)
    conv_count = sum(count for op, count in histogram.items() if op in _DLA_FRIENDLY_OPS)

    if unfriendly:
        return DlaAssessment(
            good_fit=False,
            reason=f"contains {', '.join(unfriendly)} layers that fall back to the GPU",
        )
    if matmul_count > max(4, histogram.get("Conv", 0)):
        return DlaAssessment(
            good_fit=False,
            reason=f"MatMul-heavy graph ({matmul_count} MatMul/Gemm nodes) — likely a "
            "transformer, which the DLA cannot accelerate",
        )
    if histogram.get("Conv", 0) == 0:
        return DlaAssessment(
            good_fit=False, reason="no convolution layers found — not a CNN-style model"
        )
    return DlaAssessment(
        good_fit=True,
        reason=f"convolution-dominant graph ({histogram.get('Conv', 0)} Conv, "
        f"{conv_count} DLA-native nodes) with no GPU-fallback layers",
    )
