"""Zip writing for the `blueye bundle-model` CLI.

Stdlib-only. The bundle is a flat zip: ``model.onnx``, any external weight files under
their exact embedded names, and ``model_meta.json`` — all at the archive root, matching
how BlueyeCV packages are unpacked onto the drone (``unzip -d <package_dir>``).
"""

from __future__ import annotations

import json
import logging
import zipfile
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

#: Name the model file always gets inside the bundle (the reference-package convention).
MODEL_FILE_NAME = "model.onnx"
META_FILE_NAME = "model_meta.json"

_CHUNK_SIZE = 4 * 1024 * 1024


class BundleError(Exception):
    """A user-facing bundling problem (missing files, name collisions, ...)."""


def _copy_into_zip(
    archive: zipfile.ZipFile,
    source: Path,
    arcname: str,
    progress: Callable[[int], None],
) -> None:
    """Stream one file into the archive in chunks, reporting bytes written."""
    info = zipfile.ZipInfo.from_file(source, arcname)
    info.compress_type = zipfile.ZIP_DEFLATED  # from_file defaults to ZIP_STORED
    with source.open("rb") as reader, archive.open(info, "w") as writer:
        while True:
            chunk = reader.read(_CHUNK_SIZE)
            if not chunk:
                break
            writer.write(chunk)
            progress(len(chunk))


def bundle_size(onnx_path: Path, external_files: list[str]) -> int:
    """Total input size in bytes (for progress reporting).

    Args:
        onnx_path: Path to the .onnx file.
        external_files: External-data file names living next to the .onnx.

    Raises:
        BundleError: When an external file is missing or otherwise unusable — sizing
            runs before :func:`write_bundle`, so it validates too instead of leaking a
            FileNotFoundError.
    """
    _validate_external_files(onnx_path, external_files)
    total = onnx_path.stat().st_size
    for name in external_files:
        total += (onnx_path.parent / name).stat().st_size
    return total


def _validate_external_files(onnx_path: Path, external_files: list[str]) -> None:
    """Check every external-data reference is bundleable; raise BundleError if not."""
    for name in external_files:
        if "/" in name or "\\" in name:
            raise BundleError(
                f"External data location '{name}' contains a path separator. Re-save the "
                "model with all tensors in one file next to it, e.g.:\n"
                "  onnx.save(onnx.load(p), out, save_as_external_data=True,\n"
                "            all_tensors_to_one_file=True, location='model.onnx_data')"
            )
        if name in (MODEL_FILE_NAME, META_FILE_NAME):
            raise BundleError(f"External data file '{name}' collides with a reserved bundle name.")
        if not (onnx_path.parent / name).is_file():
            raise BundleError(
                f"The model references external data file '{name}', but it was not found "
                f"next to {onnx_path.name}. Copy it into {onnx_path.parent} first."
            )


def write_bundle(
    meta: dict,
    onnx_path: Path,
    external_files: list[str],
    output_path: Path,
    progress: Callable[[int], None] | None = None,
) -> None:
    """Write the model package zip.

    The archive is written to ``<output>.part`` and atomically renamed on success, so
    an interrupted run never leaves a truncated zip behind.

    Args:
        meta: The validated model_meta dict.
        onnx_path: The source .onnx file (stored as ``model.onnx``).
        external_files: External-data file names (must exist beside the .onnx; stored
            under their exact names because the .onnx references them by name).
        output_path: Destination zip path.
        progress: Optional callback receiving the number of bytes just written.

    Raises:
        BundleError: When an external file is missing or collides with a reserved name.
    """
    progress = progress or (lambda _byte_count: None)

    _validate_external_files(onnx_path, external_files)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    partial_path = output_path.with_suffix(output_path.suffix + ".part")
    try:
        with zipfile.ZipFile(partial_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            _copy_into_zip(archive, onnx_path, MODEL_FILE_NAME, progress)
            for name in external_files:
                _copy_into_zip(archive, onnx_path.parent / name, name, progress)
            archive.writestr(META_FILE_NAME, json.dumps(meta, indent=2, ensure_ascii=False) + "\n")
        partial_path.replace(output_path)
    finally:
        partial_path.unlink(missing_ok=True)
