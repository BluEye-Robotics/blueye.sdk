"""The docs downloads must contain the same scripts as the build checkout."""

import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def test_bundle_copies_sources_and_helpers_without_bytecode(tmp_path, monkeypatch):
    def output_file(path, mode):
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        return target.open(mode)

    monkeypatch.setitem(sys.modules, "mkdocs_gen_files", SimpleNamespace(open=output_file))
    runpy.run_path(str(ROOT / "doc_utils" / "bundle_examples.py"))

    expected = {
        path.relative_to(ROOT).as_posix(): path.read_bytes()
        for path in (ROOT / "examples").rglob("*.py")
        if "__pycache__" not in path.parts
    }
    assert "examples/nmea_publisher.py" in expected
    with ZipFile(tmp_path / "examples.zip") as archive:
        assert set(archive.namelist()) == set(expected)
        for path, content in expected.items():
            assert (tmp_path / path).read_bytes() == content
            assert archive.read(path) == content
    assert not list(tmp_path.rglob("*.pyc"))
