import pytest

from blueye.sdk.cli.external import discovery
from blueye.sdk.cli.main import main

VALID_TOOL = (
    "# /// script\n"
    "# [tool.blueye]\n"
    '# name = "depth-log"\n'
    '# description = "Export depth telemetry"\n'
    "# ///\n"
    "print('hi')\n"
)


@pytest.fixture
def tools_dir(tmp_path, monkeypatch):
    directory = tmp_path / "cli-tools"
    monkeypatch.setenv(discovery.TOOLS_DIR_ENV, str(directory))
    return directory


@pytest.fixture
def tool_script(tmp_path):
    script = tmp_path / "my_script.py"
    script.write_text(VALID_TOOL)
    return script


class TestList:
    def test_lists_builtins_and_dir(self, tools_dir, capsys):
        assert main(["tools", "list"]) == 0
        out = capsys.readouterr().out
        assert "bundle-model" in out
        assert "built-in" in out
        assert str(tools_dir) in out
        assert discovery.TOOLS_DIR_ENV in out

    def test_lists_installed_and_invalid_tools(self, tools_dir, capsys):
        tools_dir.mkdir()
        (tools_dir / "good.py").write_text(VALID_TOOL)
        (tools_dir / "bad.py").write_text("no metadata\n")
        assert main(["tools", "list"]) == 0
        out = capsys.readouterr().out
        assert "depth-log" in out and "Export depth telemetry" in out
        assert "bad.py" in out and "invalid metadata" in out


class TestValidate:
    def test_valid_script_passes(self, tool_script, capsys):
        assert main(["tools", "validate", str(tool_script)]) == 0
        out = capsys.readouterr().out
        assert "ok: PEP 723 script block" in out
        assert "error:" not in out

    def test_missing_metadata_fails(self, tmp_path, capsys):
        script = tmp_path / "bad.py"
        script.write_text("print('hi')\n")
        assert main(["tools", "validate", str(script)]) == 1
        assert "error:" in capsys.readouterr().out

    def test_builtin_collision_fails(self, tmp_path, capsys):
        script = tmp_path / "sneaky.py"
        script.write_text(VALID_TOOL.replace("depth-log", "tools"))
        assert main(["tools", "validate", str(script)]) == 1
        assert "built-in" in capsys.readouterr().out

    def test_missing_file(self, tmp_path, capsys):
        assert main(["tools", "validate", str(tmp_path / "nope.py")]) == 1
        assert "no such file" in capsys.readouterr().out


class TestInstall:
    def test_install_copies_under_tool_name(self, tools_dir, tool_script, capsys):
        assert main(["tools", "install", str(tool_script)]) == 0
        assert (tools_dir / "depth-log.py").read_text() == VALID_TOOL
        out = capsys.readouterr().out
        assert "Installed 'depth-log'" in out
        assert "blueye depth-log" in out

    def test_install_refuses_overwrite_without_force(self, tools_dir, tool_script, capsys):
        assert main(["tools", "install", str(tool_script)]) == 0
        assert main(["tools", "install", str(tool_script)]) == 1
        assert "--force" in capsys.readouterr().err

    def test_install_force_overwrites(self, tools_dir, tool_script):
        assert main(["tools", "install", str(tool_script)]) == 0
        tool_script.write_text(VALID_TOOL.replace("Export depth telemetry", "v2"))
        assert main(["tools", "install", str(tool_script), "--force"]) == 0
        assert "v2" in (tools_dir / "depth-log.py").read_text()

    def test_install_rejects_invalid_script(self, tools_dir, tmp_path, capsys):
        script = tmp_path / "bad.py"
        script.write_text("nope\n")
        assert main(["tools", "install", str(script)]) == 1
        assert "not a valid blueye tool" in capsys.readouterr().err

    def test_install_rejects_builtin_name(self, tools_dir, tmp_path, capsys):
        script = tmp_path / "sneaky.py"
        script.write_text(VALID_TOOL.replace("depth-log", "bundle-model"))
        assert main(["tools", "install", str(script)]) == 1
        assert "built-in" in capsys.readouterr().err


class TestUninstall:
    def test_uninstall_by_name(self, tools_dir, tool_script):
        main(["tools", "install", str(tool_script)])
        assert main(["tools", "uninstall", "depth-log"]) == 0
        assert not (tools_dir / "depth-log.py").exists()

    def test_uninstall_hand_copied_file_by_metadata_name(self, tools_dir):
        tools_dir.mkdir()
        (tools_dir / "renamed_by_hand.py").write_text(VALID_TOOL)
        assert main(["tools", "uninstall", "depth-log"]) == 0
        assert not (tools_dir / "renamed_by_hand.py").exists()

    def test_uninstall_unknown_lists_installed(self, tools_dir, tool_script, capsys):
        main(["tools", "install", str(tool_script)])
        assert main(["tools", "uninstall", "nope"]) == 1
        err = capsys.readouterr().err
        assert "depth-log" in err


class TestDir:
    def test_prints_resolved_dir(self, tools_dir, capsys):
        assert main(["tools", "dir"]) == 0
        captured = capsys.readouterr()
        assert captured.out.strip() == str(tools_dir)
        assert "does not exist yet" in captured.err


class TestPerCommandGate:
    def test_tools_needs_no_extras(self, tools_dir, mocker):
        """`tools` must run even when the [cli] extra is reported missing."""

        def fake_missing(names):
            return [name for name in ("onnx", "rich", "questionary") if name in names]

        mocker.patch("blueye.sdk.cli.deps.missing", side_effect=fake_missing)
        assert main(["tools", "list"]) == 0
        assert main(["bundle-model", "x.onnx"]) == 2
