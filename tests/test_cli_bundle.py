import json
import zipfile

import pytest

from blueye.sdk.cli.commands.bundle_model.bundle import BundleError, bundle_size, write_bundle

META = {"format_version": 1, "model_file": "model.onnx", "labels": ["x"]}


@pytest.fixture
def onnx_file(tmp_path):
    path = tmp_path / "exported_yolo.onnx"
    path.write_bytes(b"onnx-bytes" * 1000)
    return path


def test_zip_contains_exactly_root_level_files(onnx_file, tmp_path):
    output = tmp_path / "out.zip"
    write_bundle(META, onnx_file, [], output)

    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist()) == ["model.onnx", "model_meta.json"]
        assert archive.read("model.onnx") == onnx_file.read_bytes()
        assert json.loads(archive.read("model_meta.json")) == META


def test_external_data_included_under_exact_name(onnx_file, tmp_path):
    (tmp_path / "model.onnx_data").write_bytes(b"weights" * 100)
    output = tmp_path / "out.zip"
    write_bundle(META, onnx_file, ["model.onnx_data"], output)

    with zipfile.ZipFile(output) as archive:
        assert "model.onnx_data" in archive.namelist()


def test_missing_external_data_raises(onnx_file, tmp_path):
    with pytest.raises(BundleError, match="not found"):
        write_bundle(META, onnx_file, ["model.onnx_data"], tmp_path / "out.zip")


def test_external_data_with_path_separator_raises(onnx_file, tmp_path):
    with pytest.raises(BundleError, match="path separator"):
        write_bundle(META, onnx_file, ["weights/model.onnx_data"], tmp_path / "out.zip")


def test_external_data_name_collision_raises(onnx_file, tmp_path):
    with pytest.raises(BundleError, match="reserved"):
        write_bundle(META, onnx_file, ["model_meta.json"], tmp_path / "out.zip")


def test_no_partial_file_left_behind(onnx_file, tmp_path):
    output = tmp_path / "out.zip"
    write_bundle(META, onnx_file, [], output)
    assert output.exists()
    assert not (tmp_path / "out.zip.part").exists()


def test_partial_cleaned_up_on_failure(onnx_file, tmp_path):
    output = tmp_path / "out.zip"
    with pytest.raises(BundleError):
        write_bundle(META, onnx_file, ["missing_file"], output)
    assert not output.exists()
    assert not (tmp_path / "out.zip.part").exists()


def test_progress_reports_all_bytes(onnx_file, tmp_path):
    (tmp_path / "model.onnx_data").write_bytes(b"w" * 4096)
    seen = []
    write_bundle(
        META,
        onnx_file,
        ["model.onnx_data"],
        tmp_path / "out.zip",
        progress=seen.append,
    )
    assert sum(seen) == bundle_size(onnx_file, ["model.onnx_data"])


def test_bundle_size_raises_for_missing_external_file(onnx_file):
    # bundle_size runs before write_bundle's checks; it must not leak a
    # FileNotFoundError past the BundleError handler.
    with pytest.raises(BundleError, match="not found"):
        bundle_size(onnx_file, ["model.onnx_data"])
