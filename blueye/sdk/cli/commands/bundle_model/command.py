"""The `blueye bundle-model` subcommand.

Bundles an ONNX model plus an auto-generated ``model_meta.json`` into a zip that can be
deployed as a BlueyeCV model package. Argument definitions are stdlib-only; everything
that needs the ``[cli]`` extra is imported inside :func:`run`, after the dependency
gate in ``main``.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from pathlib import Path

from ...errors import CliError

logger = logging.getLogger(__name__)

#: Devices the drone's CV model API exposes; the interactive prompt offers only these.
_DRONE_DEVICES = ("cuda", "tensorrt", "tensorrt-dla0", "tensorrt-dla1")
#: The package format additionally allows cpu/coreml for local desktop testing with
#: be-cv; they stay reachable via an explicit --runtime-device flag.
_DEVICES = (*_DRONE_DEVICES, "cpu", "coreml")
_RATE_PRESETS = ("max (unlimited)", "30", "15", "10", "5", "2", "custom...")


def add_parser(subparsers) -> None:
    """Register the ``bundle-model`` subcommand on the ``blueye`` parser."""
    parser = subparsers.add_parser(
        "bundle-model",
        help="Bundle an ONNX model into a BlueyeCV model-package zip",
        description=(
            "Validate an ONNX model, auto-generate its model_meta.json, and bundle both "
            "into a zip ready to deploy on a Blueye drone. Run without options for a "
            "guided interactive session; every prompt can also be answered with a flag."
        ),
    )
    parser.add_argument("onnx_path", nargs="?", help="Path to the ONNX model file")
    parser.add_argument("--name", help="Human-readable model name")
    parser.add_argument(
        "--model-version",
        help='Model version string written to the metadata (default: "1.0.0")',
    )
    parser.add_argument("--description", help="Human-readable model description")
    parser.add_argument("--author", help="Model author/publisher")
    parser.add_argument(
        "--license",
        help='Model license, preferably an SPDX id (e.g. "MIT", "Apache-2.0", "Proprietary")',
    )
    parser.add_argument("-o", "--output", help="Output zip path (default: <name>_package.zip)")
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=[
            "yolov2_grid",
            "yolov5_flat",
            "yolov8_flat",
            "yolov8_seg",
            "yolo_e2e",
            "yolo_e2e_seg",
            "ssd_multi",
            "detr",
            "ostrack",
            "mixformerv2",
        ],
        help="Decoder format (default: inferred from the model)",
    )
    parser.add_argument("--labels", help="Path to a labels file (one class name per line)")
    parser.add_argument("--num-classes", type=int, help="Number of object classes")
    parser.add_argument("--input-size", metavar="WxH", help="Model input size, e.g. 640x640")
    parser.add_argument(
        "--anchors",
        help='Anchor pairs for yolov2_grid, e.g. "1.08,1.19 3.42,4.41" (grid-cell units)',
    )
    parser.add_argument("--grid-size", type=int, help="Grid size for yolov2_grid")
    parser.add_argument(
        "--one-indexed-classes",
        action="store_true",
        help="Class IDs start at 1 (TensorFlow SSD exports)",
    )
    parser.add_argument("--color-order", choices=["rgb", "bgr"], help="Model channel order")
    parser.add_argument("--normalize-scale", type=float, help="Pixel scale (1/255 or 1.0)")
    parser.add_argument("--normalize-mean", help="Per-channel mean, e.g. 0.485,0.456,0.406")
    parser.add_argument("--normalize-std", help="Per-channel std, e.g. 0.229,0.224,0.225")
    parser.add_argument("--confidence-threshold", type=float, help="Detection confidence threshold")
    parser.add_argument("--nms-threshold", type=float, help="NMS IoU threshold")
    parser.add_argument(
        "--tracking",
        choices=["none", "iou", "byte_track"],
        help="Multi-object tracking algorithm (detection packages)",
    )
    parser.add_argument(
        "--runtime-device", choices=list(_DEVICES), help="Execution provider on the drone"
    )
    parser.add_argument("--runtime-hz", help='Maximum inference rate in Hz, or "max" for unlimited')
    parser.add_argument(
        "--runtime-enabled",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Autolaunch this package on the drone (default: enabled; use "
        "--no-runtime-enabled to bundle it disabled)",
    )
    parser.add_argument("--template-size", type=int, help="SOT template crop size (px)")
    parser.add_argument("--search-size", type=int, help="SOT search region size (px)")
    parser.add_argument(
        "-y", "--yes", action="store_true", help="Accept all inferred defaults, no prompts"
    )
    parser.add_argument(
        "--push", action="store_true", help="Upload the bundle to the drone after writing it"
    )
    parser.add_argument(
        "--drone-ip",
        default="192.168.1.101",
        help="Drone address used by --push (default: %(default)s)",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing zip")
    parser.add_argument(
        "--dry-run", action="store_true", help="Print the generated model_meta.json and stop"
    )
    parser.add_argument(
        "--strict", action="store_true", help="Treat onnx.checker failures as fatal"
    )
    parser.add_argument("--quiet", action="store_true", help="Only errors and the result path")


def _sanitize_name(name: str) -> str:
    """Turn a model name into a filesystem-friendly package stem."""
    stem = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return stem or "model"


def _parse_input_size(value: str):
    match = re.fullmatch(r"(\d+)[xX](\d+)", value.strip())
    if not match:
        raise CliError(f'--input-size must look like "640x640", got "{value}"')
    return int(match.group(1)), int(match.group(2))


def _parse_anchors(value: str) -> list[list[float]]:
    anchors = []
    for pair in value.replace(";", " ").split():
        parts = pair.split(",")
        if len(parts) != 2:
            raise CliError(f'--anchors pairs must be "w,h", got "{pair}"')
        try:
            anchors.append([float(parts[0]), float(parts[1])])
        except ValueError as error:
            raise CliError(f'--anchors values must be numbers, got "{pair}"') from error
    return anchors


def _parse_hz(value: str, flag: str) -> float:
    try:
        return float(value)
    except ValueError as error:
        raise CliError(
            f'{flag} must be a number (or "max" for unlimited), got "{value}"'
        ) from error


def _parse_float_list(value: str, flag: str) -> list[float]:
    try:
        return [float(part) for part in value.split(",") if part.strip()]
    except ValueError as error:
        raise CliError(f"{flag} must be a comma-separated float list: {error}") from error


def _optional_text(value: str | None, prompter, interactive: bool, question: str, flag: str) -> str:
    """Resolve an optional informational field: the flag wins, interactive runs prompt,
    non-interactive runs omit the field instead of failing on the empty default."""
    if value is not None:
        return value
    if not interactive:
        return ""
    return prompter.text(question, "", flag)


def _read_labels_file(path: Path) -> list[str]:
    if not path.is_file():
        raise CliError(f"Labels file not found: {path}")
    labels = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
    return [label for label in labels if label]


def _resolve_labels(args, config, prompter, console) -> list[str]:
    """Resolve the labels list from flags, embedded metadata, or prompts."""
    if args.labels:
        labels = _read_labels_file(Path(args.labels))
    elif config.labels and config.kind != "sot":
        preview = ", ".join(config.labels[:5]) + ("..." if len(config.labels) > 5 else "")
        use_embedded = prompter.confirm(
            f"Use the {len(config.labels)} embedded labels ({preview})?", True, "--labels"
        )
        labels = list(config.labels) if use_embedded else []
        if not labels:
            path = prompter.path("Path to a labels file (one name per line):", None, "--labels")
            labels = _read_labels_file(Path(path))
    elif config.kind == "sot":
        return ["tracked"]
    else:
        path = prompter.path("Path to a labels file (one name per line):", None, "--labels")
        labels = _read_labels_file(Path(path))

    num_classes = config.num_classes
    if num_classes is not None and len(labels) != num_classes:
        console.print(
            f"[yellow]The model implies {num_classes} classes but {len(labels)} labels "
            "were provided.[/yellow]"
        )
        pad = prompter.confirm(
            f"Pad/truncate the labels to {num_classes} entries?", False, "--labels"
        )
        if not pad:
            raise CliError(
                f"Label count mismatch: {len(labels)} labels vs {num_classes} classes. "
                "Provide a matching --labels file (DETR-style models include a leading "
                '"N/A" no-object label).'
            )
        labels = (labels + [f"class_{i}" for i in range(len(labels), num_classes)])[:num_classes]
    return labels


def _resolve_runtime(args, dla, prompter):
    """Resolve the runtime block: device (with DLA recommendation), rate, autolaunch."""
    if args.runtime_device:
        device = args.runtime_device
    else:
        recommended = "tensorrt-dla0" if dla.good_fit else "tensorrt"
        choices = [
            device + (" (recommended)" if device == recommended else "")
            for device in _DRONE_DEVICES
        ]
        answer = prompter.select(
            f"Execution device on the drone? ({dla.reason})",
            choices,
            recommended + " (recommended)",
            "--runtime-device",
        )
        device = answer.replace(" (recommended)", "")

    if args.runtime_hz:
        hz = (
            None if args.runtime_hz.lower() == "max" else _parse_hz(args.runtime_hz, "--runtime-hz")
        )
    else:
        answer = prompter.select(
            "Maximum inference rate?", list(_RATE_PRESETS), _RATE_PRESETS[0], "--runtime-hz"
        )
        if answer.startswith("max"):
            hz = None
        elif answer == "custom...":
            hz = _parse_hz(prompter.text("Rate in Hz:", "10", "--runtime-hz"), "the rate")
        else:
            hz = _parse_hz(answer, "--runtime-hz")

    if args.runtime_enabled is not None:
        enabled = args.runtime_enabled
    else:
        enabled = prompter.confirm(
            "Autolaunch this package on the drone (runtime.enabled)?",
            True,
            "--runtime-enabled/--no-runtime-enabled",
        )
    return device, hz, enabled


def _push_to_drone(console, zip_path: Path, ip: str) -> None:
    """Upload the bundle to the drone, translating failures into CliErrors."""
    import requests

    from blueye.sdk import Drone

    drone = Drone(ip=ip, auto_connect=False)  # HTTP only; takes no control of the drone.
    try:
        with console.status(f"[cyan]Uploading to the drone at {ip}..."):
            model = drone.cv_models.upload(zip_path)
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as error:
        raise CliError(
            f"Could not reach the drone at {ip} — is it connected? The bundle was written "
            f"to {zip_path}; connect to the drone and re-run with --push, use "
            "`blueye models upload`, or upload it in the drone's web UI."
        ) from error
    except requests.exceptions.HTTPError as error:
        raise CliError(
            f"The drone rejected the package: {error}. The bundle was written to {zip_path}."
        ) from error

    state = "enabled" if model.enabled else "disabled"
    console.print(
        f"[green bold]Uploaded to the drone:[/green bold] '{model.name}' installed as "
        f"'{model.directory}' (autolaunch {state})"
    )
    console.print(
        f"[dim]Tip: `blueye models warmup {model.directory}` pre-builds the inference "
        "engine so the first launch is instant.[/dim]"
    )


def run(args: argparse.Namespace) -> int:
    """Run the bundle-model subcommand. Returns the process exit code."""
    from ... import prompts, ui
    from . import bundle, heuristics, introspect, meta

    console = ui.make_console(quiet=args.quiet)
    interactive = not args.yes and sys.stdin.isatty() and sys.stdout.isatty()
    prompter = prompts.QuestionaryPrompter() if interactive else prompts.NonInteractivePrompter()

    try:
        # Stage 0 — resolve the input path.
        onnx_path = Path(
            args.onnx_path or prompter.path("Path to the ONNX model:", None, "ONNX_PATH")
        ).expanduser()

        # Stage 1 — load and check.
        with console.status("[cyan]Loading ONNX model..."):
            info = introspect.load_model_info(onnx_path)
        console.print(ui.model_summary_panel(info))

        with console.status("[cyan]Running the ONNX checker..."):
            check_error = introspect.check_model(onnx_path)
        if check_error is not None:
            first_line = check_error.splitlines()[0]
            if args.strict:
                raise CliError(f"onnx.checker failed: {first_line}")
            console.print(f"[yellow]onnx.checker warning:[/yellow] {first_line}")
            if not prompter.confirm("Continue anyway?", True, "--strict"):
                return 1

        # Stage 2 — infer the configuration.
        with console.status("[cyan]Analyzing model outputs..."):
            config = heuristics.infer(info)
            dla = heuristics.assess_dla_fitness(info)
        console.print(ui.inference_panel(config))

        # Stage 3 — confirm / collect.
        output_format = args.output_format or config.output_format
        if output_format is None or (
            not args.output_format and config.confidence == "low" and interactive
        ):
            output_format = prompter.select(
                "Model output format?",
                list(heuristics.ALL_FORMATS),
                config.output_format,
                "--format",
            )
        kind = "sot" if output_format in heuristics.SOT_FORMATS else "detection"

        default_name = args.name or config.suggested_name or onnx_path.stem
        name = args.name or prompter.text("Model name:", default_name, "--name")

        options = meta.MetaOptions(name=name, output_format=output_format, kind=kind)

        options.version = args.model_version or prompter.text(
            "Model version:", "1.0.0", "--model-version"
        )
        has_detail_flags = any(
            value is not None for value in (args.description, args.author, args.license)
        )
        if has_detail_flags or prompter.confirm(
            "Add package details (description / author / license)?", False, "--description"
        ):
            options.description = _optional_text(
                args.description, prompter, interactive, "Description:", "--description"
            )
            options.author = _optional_text(
                args.author, prompter, interactive, "Author:", "--author"
            )
            options.license = _optional_text(
                args.license,
                prompter,
                interactive,
                "License (SPDX id, e.g. MIT, Apache-2.0, AGPL-3.0, Proprietary):",
                "--license",
            )

        if args.input_size:
            options.input_width, options.input_height = _parse_input_size(args.input_size)
        else:
            options.input_width = config.input_width
            options.input_height = config.input_height
        needs_size = kind == "detection" and (
            output_format in meta.FORMATS_REQUIRING_INPUT_SIZE or output_format == "yolov2_grid"
        )
        if needs_size and (options.input_width is None or options.input_height is None):
            size = prompter.text(
                "Model input size (WxH, the model has dynamic dims):", "640x640", "--input-size"
            )
            options.input_width, options.input_height = _parse_input_size(size)

        if kind == "detection":
            options.num_classes = args.num_classes or config.num_classes
            config.num_classes = options.num_classes
            options.labels = _resolve_labels(args, config, prompter, console)
            if options.num_classes is None:
                options.num_classes = len(options.labels)

            if output_format == "yolov2_grid":
                anchors_text = args.anchors or prompter.text(
                    'Anchor pairs in grid-cell units (e.g. "1.08,1.19 3.42,4.41"):',
                    "",
                    "--anchors",
                )
                options.anchors = _parse_anchors(anchors_text)
                options.grid_size = args.grid_size or config.grid_size
                if not options.grid_size:
                    options.grid_size = int(
                        prompter.text("Feature-map grid size:", "13", "--grid-size")
                    )
            if output_format == "ssd_multi":
                options.one_indexed_classes = args.one_indexed_classes or prompter.confirm(
                    "Are class IDs one-indexed (TensorFlow SSD exports)?",
                    False,
                    "--one-indexed-classes",
                )
            if args.confidence_threshold is not None:
                options.confidence_threshold = args.confidence_threshold
            if args.nms_threshold is not None:
                options.nms_threshold = args.nms_threshold

            tracking = args.tracking or prompter.select(
                "Multi-object tracking?", ["none", "iou", "byte_track"], "none", "--tracking"
            )
            options.tracking_algorithm = tracking
        else:
            options.template_size = args.template_size or config.template_size
            options.search_size = args.search_size or config.search_size
            options.labels = ["tracked"]

        # Preprocessing: per-format defaults, customizable.
        scale, mean, std = meta.default_preprocessing(output_format)
        options.normalize_scale = scale
        options.normalize_mean = mean
        options.normalize_std = std
        has_preproc_flags = any(
            value is not None
            for value in (
                args.color_order,
                args.normalize_scale,
                args.normalize_mean,
                args.normalize_std,
            )
        )
        if has_preproc_flags or prompter.confirm(
            "Customize preprocessing (color order / normalization)?", False, "--color-order"
        ):
            options.color_order = args.color_order or prompter.select(
                "Channel order the model expects?", ["rgb", "bgr"], "rgb", "--color-order"
            )
            if args.normalize_scale is not None:
                options.normalize_scale = args.normalize_scale
            else:
                scale_answer = prompter.select(
                    "Pixel normalization?",
                    ["1/255 (inputs in [0,1])", "1.0 (raw 0-255 pixels)"],
                    "1/255 (inputs in [0,1])" if scale != 1.0 else "1.0 (raw 0-255 pixels)",
                    "--normalize-scale",
                )
                options.normalize_scale = (
                    meta.SCALE_1_OVER_255 if scale_answer.startswith("1/255") else 1.0
                )
            if args.normalize_mean is not None:
                options.normalize_mean = _parse_float_list(args.normalize_mean, "--normalize-mean")
            if args.normalize_std is not None:
                options.normalize_std = _parse_float_list(args.normalize_std, "--normalize-std")

        # Runtime block (always collected; DLA recommendation, rate, autolaunch).
        device, hz, enabled = _resolve_runtime(args, dla, prompter)
        options.runtime_device = device
        options.runtime_hz = hz
        options.runtime_enabled = enabled
        if device not in _DRONE_DEVICES:
            console.print(
                f"[yellow]Note:[/yellow] device '{device}' is for local be-cv testing — "
                f"the drone only exposes {', '.join(_DRONE_DEVICES)}."
            )

        # Stage 4 — build and validate.
        meta_dict = meta.build_meta(options)
        problems = meta.validate_meta(meta_dict)
        if problems:
            for problem in problems:
                console.print(f"[red]invalid metadata:[/red] {problem}")
            return 1

        if args.dry_run:
            console.print(ui.meta_preview(meta_dict))
            return 0

        # Stage 5 — write the zip.
        default_output = f"{_sanitize_name(name)}_package.zip"
        output_path = Path(
            args.output or prompter.text("Output zip path:", default_output, "--output")
        ).expanduser()
        # Overwriting is destructive: non-interactive runs (--yes / no TTY) must opt
        # in explicitly with --force; interactively the confirm defaults to No.
        if output_path.exists() and not args.force:
            if not interactive:
                raise CliError(f"{output_path} already exists (pass --force to overwrite it).")
            if not prompter.confirm(f"{output_path} exists — overwrite?", False, "--force"):
                raise CliError(f"{output_path} already exists (use --force to overwrite).")

        external_files = list(info.external_data_files)
        total = bundle.bundle_size(onnx_path, external_files)
        with ui.make_progress(console) as progress:
            task = progress.add_task("Writing bundle", total=total)
            bundle.write_bundle(
                meta_dict,
                onnx_path,
                external_files,
                output_path,
                progress=lambda byte_count: progress.update(task, advance=byte_count),
            )

        size_mb = output_path.stat().st_size / (1024 * 1024)
        contents = ", ".join([bundle.MODEL_FILE_NAME, *external_files, bundle.META_FILE_NAME])
        console.print()
        console.print(f"[green bold]Bundle written:[/green bold] {output_path} ({size_mb:.1f} MB)")
        console.print(f"[dim]Contents: {contents}[/dim]")

        # Stage 6 — optionally push the package to the drone.
        push = args.push or (
            interactive
            and prompter.confirm(
                f"Upload the package to the drone at {args.drone_ip} now?", False, "--push"
            )
        )
        if push:
            _push_to_drone(console, output_path, args.drone_ip)
        else:
            console.print(
                f"[dim]Deploy: re-run with --push (drone at {args.drone_ip}), use "
                "`blueye models upload`, or upload the zip in the drone's web UI.[/dim]"
            )
        return 0

    except (introspect.IntrospectionError, heuristics.UnsupportedModelError) as error:
        console.print(f"[red]Error:[/red] {error}")
        return 1
    except bundle.BundleError as error:
        console.print(f"[red]Error:[/red] {error}")
        return 1
    except prompts.PromptAborted:
        console.print("[yellow]Cancelled.[/yellow]")
        return 130
