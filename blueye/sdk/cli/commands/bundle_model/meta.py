"""model_meta.json construction and validation.

Pure, stdlib-only functions implementing the BlueyeCV model package contract
(BlueyeCV/docs/model-meta-spec.md). The generated JSON mirrors the field order used by
the reference packages so diffs against hand-written files stay readable.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

#: Formats whose decoders require input_width/input_height in the metadata.
FORMATS_REQUIRING_INPUT_SIZE = (
    "yolov5_flat",
    "yolov8_flat",
    "yolov8_seg",
    "yolo_e2e",
    "yolo_e2e_seg",
    "detr",
)

#: Default 1/255 pixel scale, written with the same precision as the reference packages.
SCALE_1_OVER_255 = 0.00392156862

#: ImageNet normalization used by DETR and the SOT models.
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

#: Per-format SOT defaults, taken from the reference ostrack/mixformerv2 packages.
SOT_DEFAULTS = {
    "ostrack": {
        "template_size": 128,
        "search_size": 256,
        "template_crop_factor": 2.0,
        "search_crop_factor": 4.0,
        "confidence_threshold": 0.5,
        "hann_window": True,
        "template_update_interval": 0,
        "search_expand_rate": 1.2,
        "search_max_factor": 8.0,
    },
    "mixformerv2": {
        "template_size": 112,
        "search_size": 224,
        "template_crop_factor": 2.0,
        "search_crop_factor": 4.5,
        "confidence_threshold": 0.5,
        "hann_window": False,
        "template_update_interval": 15,
        "search_expand_rate": 1.2,
        "search_max_factor": 8.0,
        "max_lost_frames": 10,
        "distance_gate_factor": 5.0,
    },
}

#: Default tracking parameters per algorithm (from the spec).
TRACKING_DEFAULTS = {
    "iou": {"max_age": 50, "min_hits": 1, "iou_threshold": 0.2},
    "byte_track": {
        "max_age": 50,
        "min_hits": 1,
        "iou_threshold": 0.2,
        "high_threshold": 0.5,
        "low_threshold": 0.1,
    },
}


@dataclass
class MetaOptions:
    """Everything needed to build a model_meta.json, after prompting/flags.

    Attributes mirror the spec's blocks; None/empty means "omit or use the default".
    """

    name: str = ""
    output_format: str = ""
    kind: str = "detection"  # "detection" or "sot"
    num_classes: int | None = None
    labels: list[str] = field(default_factory=list)
    input_width: int | None = None
    input_height: int | None = None
    grid_size: int | None = None
    anchors: list[list[float]] = field(default_factory=list)
    confidence_threshold: float = 0.3
    nms_threshold: float = 0.45
    one_indexed_classes: bool = False
    # Preprocessing.
    color_order: str = "rgb"
    normalize_scale: float = SCALE_1_OVER_255
    normalize_mean: list[float] = field(default_factory=list)
    normalize_std: list[float] = field(default_factory=list)
    # SOT.
    template_size: int | None = None
    search_size: int | None = None
    sot_overrides: dict[str, object] = field(default_factory=dict)
    # Tracking (detection only).
    tracking_algorithm: str = "none"
    tracking_overrides: dict[str, object] = field(default_factory=dict)
    # Runtime.
    runtime_device: str | None = None
    runtime_hz: float | None = None
    runtime_enabled: bool = False


def default_preprocessing(output_format: str) -> tuple[float, list[float], list[float]]:
    """Return (normalize_scale, normalize_mean, normalize_std) defaults per format.

    Matches every reference package: YOLOv2 and TF-SSD models take raw 0-255 pixels,
    DETR and the SOT trackers use ImageNet normalization, everything else scales to
    [0, 1].
    """
    if output_format in ("yolov2_grid", "ssd_multi"):
        return 1.0, [], []
    if output_format in ("detr", "ostrack", "mixformerv2"):
        return SCALE_1_OVER_255, list(IMAGENET_MEAN), list(IMAGENET_STD)
    return SCALE_1_OVER_255, [], []


def build_meta(options: MetaOptions) -> dict:
    """Build the model_meta.json dict from the collected options.

    Args:
        options: The fully-resolved options (inference results merged with prompt/flag
            answers).

    Returns:
        A JSON-serializable dict in the reference packages' field order.
    """
    meta: dict = {
        "format_version": 1,
        "model_file": "model.onnx",
        "name": options.name,
    }

    preprocessing: dict = {
        "color_order": options.color_order,
        "normalize_scale": options.normalize_scale,
    }
    if options.normalize_mean:
        preprocessing["normalize_mean"] = options.normalize_mean
    if options.normalize_std:
        preprocessing["normalize_std"] = options.normalize_std
    meta["preprocessing"] = preprocessing

    if options.kind == "sot":
        sot: dict = {"output_format": options.output_format}
        defaults = dict(SOT_DEFAULTS.get(options.output_format, SOT_DEFAULTS["ostrack"]))
        if options.template_size is not None:
            defaults["template_size"] = options.template_size
        if options.search_size is not None:
            defaults["search_size"] = options.search_size
        defaults.update(options.sot_overrides)
        sot.update(defaults)
        meta["sot"] = sot
    else:
        detection: dict = {"output_format": options.output_format}
        if options.output_format == "yolov2_grid":
            detection["anchors"] = options.anchors
            detection["grid_size"] = options.grid_size
        detection["num_classes"] = options.num_classes
        if options.input_width is not None and options.input_height is not None:
            detection["input_width"] = options.input_width
            detection["input_height"] = options.input_height
        detection["confidence_threshold"] = options.confidence_threshold
        detection["nms_threshold"] = options.nms_threshold
        if options.one_indexed_classes:
            detection["one_indexed_classes"] = True
        meta["detection"] = detection

        if options.tracking_algorithm not in ("", "none"):
            tracking: dict = {"algorithm": options.tracking_algorithm}
            tracking.update(TRACKING_DEFAULTS.get(options.tracking_algorithm, {}))
            tracking.update(options.tracking_overrides)
            meta["tracking"] = tracking

    if options.runtime_device is not None or options.runtime_hz is not None:
        runtime: dict = {"enabled": options.runtime_enabled}
        if options.runtime_device is not None:
            runtime["device"] = options.runtime_device
        if options.runtime_hz is not None:
            runtime["hz"] = options.runtime_hz
        meta["runtime"] = runtime

    meta["labels"] = options.labels if options.labels else ["tracked"]
    return meta


def validate_meta(meta: dict) -> list[str]:
    """Check a model_meta dict against the BlueyeCV parser's validation rules.

    Args:
        meta: The dict produced by :func:`build_meta` (or hand-assembled).

    Returns:
        A list of human-readable problems; empty when the metadata is valid.
    """
    errors: list[str] = []
    if meta.get("format_version") != 1:
        errors.append("format_version must be 1")
    if not meta.get("model_file"):
        errors.append("model_file must be non-empty")

    detection = meta.get("detection")
    sot = meta.get("sot")
    if detection is None and sot is None:
        errors.append("at least one of 'detection' or 'sot' must be present")

    if detection is not None:
        output_format = detection.get("output_format", "")
        if not output_format:
            errors.append("detection.output_format must be non-empty")
        num_classes = detection.get("num_classes", 0)
        if not isinstance(num_classes, int) or num_classes <= 0:
            errors.append("detection.num_classes must be a positive integer")
        labels = meta.get("labels", [])
        if isinstance(num_classes, int) and num_classes > 0 and len(labels) != num_classes:
            errors.append(
                f"labels has {len(labels)} entries but detection.num_classes is {num_classes}"
            )
        if output_format == "yolov2_grid":
            anchors = detection.get("anchors", [])
            if not anchors:
                errors.append("yolov2_grid requires a non-empty detection.anchors list")
            elif any(len(pair) != 2 for pair in anchors):
                errors.append("detection.anchors entries must be [width, height] pairs")
            if not detection.get("grid_size"):
                errors.append("yolov2_grid requires detection.grid_size > 0")
        if output_format in FORMATS_REQUIRING_INPUT_SIZE:
            if not detection.get("input_width") or not detection.get("input_height"):
                errors.append(
                    f"{output_format} requires detection.input_width and " "detection.input_height"
                )

    if sot is not None:
        if not sot.get("output_format"):
            errors.append("sot.output_format must be non-empty")
        if not isinstance(sot.get("template_size"), int) or sot.get("template_size", 0) <= 0:
            errors.append("sot.template_size must be > 0")
        if not isinstance(sot.get("search_size"), int) or sot.get("search_size", 0) <= 0:
            errors.append("sot.search_size must be > 0")

    return errors
