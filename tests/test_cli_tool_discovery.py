from pathlib import Path

import pytest

from blueye.sdk.cli.external import discovery


def tool_source(name: str, description: str = "A tool") -> str:
    return (
        "# /// script\n"
        "# [tool.blueye]\n"
        f'# name = "{name}"\n'
        f'# description = "{description}"\n'
        "# ///\n"
        "print('hi')\n"
    )


@pytest.fixture
def tools_dir(tmp_path, monkeypatch):
    directory = tmp_path / "cli-tools"
    directory.mkdir()
    monkeypatch.setenv(discovery.TOOLS_DIR_ENV, str(directory))
    return directory


class TestToolsDirResolution:
    def test_env_var_wins(self, monkeypatch, tmp_path):
        monkeypatch.setenv(discovery.TOOLS_DIR_ENV, str(tmp_path / "custom"))
        assert discovery.tools_dir() == tmp_path / "custom"
        assert discovery.TOOLS_DIR_ENV in discovery.tools_dir_source()

    def test_macos_default(self, monkeypatch):
        monkeypatch.delenv(discovery.TOOLS_DIR_ENV, raising=False)
        monkeypatch.setattr("sys.platform", "darwin")
        expected = Path.home() / "Library" / "Application Support" / "blueye" / "cli-tools"
        assert discovery.tools_dir() == expected

    def test_linux_xdg_default(self, monkeypatch, tmp_path):
        monkeypatch.delenv(discovery.TOOLS_DIR_ENV, raising=False)
        monkeypatch.setattr("sys.platform", "linux")
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        assert discovery.tools_dir() == tmp_path / "xdg" / "blueye" / "cli-tools"

    def test_linux_without_xdg(self, monkeypatch):
        monkeypatch.delenv(discovery.TOOLS_DIR_ENV, raising=False)
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setattr("sys.platform", "linux")
        expected = Path.home() / ".local" / "share" / "blueye" / "cli-tools"
        assert discovery.tools_dir() == expected

    def test_windows_appdata(self, monkeypatch, tmp_path):
        monkeypatch.delenv(discovery.TOOLS_DIR_ENV, raising=False)
        monkeypatch.setattr("sys.platform", "win32")
        monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))
        assert discovery.tools_dir() == tmp_path / "AppData" / "blueye" / "cli-tools"


class TestScanning:
    def test_missing_dir_is_empty(self, monkeypatch, tmp_path):
        monkeypatch.setenv(discovery.TOOLS_DIR_ENV, str(tmp_path / "nope"))
        assert discovery.scan_tools_dir() == []
        assert discovery.discover_tools() == {}

    def test_valid_tool_discovered(self, tools_dir):
        (tools_dir / "export.py").write_text(tool_source("export-logs"))
        tools = discovery.discover_tools()
        assert set(tools) == {"export-logs"}
        assert tools["export-logs"].path.name == "export.py"

    def test_invalid_tool_excluded_but_scanned(self, tools_dir):
        (tools_dir / "broken.py").write_text("print('no metadata')\n")
        assert discovery.discover_tools() == {}
        scanned = discovery.scan_tools_dir()
        assert len(scanned) == 1
        assert scanned[0].metadata is None
        assert "script" in scanned[0].error

    def test_non_py_files_ignored(self, tools_dir):
        (tools_dir / "readme.txt").write_text("hello")
        (tools_dir / "tool.sh").write_text("#!/bin/sh")
        assert discovery.scan_tools_dir() == []

    def test_duplicate_names_first_file_wins(self, tools_dir):
        (tools_dir / "a.py").write_text(tool_source("dupe"))
        (tools_dir / "b.py").write_text(tool_source("dupe"))
        tools = discovery.discover_tools()
        assert tools["dupe"].path.name == "a.py"
        shadowed = [tool for tool in discovery.scan_tools_dir() if tool.shadowed_by]
        assert len(shadowed) == 1
        assert shadowed[0].shadowed_by == "a.py"

    def test_builtin_collision_shadowed(self, tools_dir):
        (tools_dir / "sneaky.py").write_text(tool_source("tools"))
        assert discovery.discover_tools(frozenset({"tools"})) == {}
        scanned = discovery.scan_tools_dir(frozenset({"tools"}))
        assert scanned[0].shadowed_by == "built-in command"

    def test_symlinked_script_followed(self, tools_dir, tmp_path):
        real = tmp_path / "real_tool.py"
        real.write_text(tool_source("linked"))
        (tools_dir / "linked.py").symlink_to(real)
        assert "linked" in discovery.discover_tools()


class TestEpilog:
    def test_empty_tools_no_epilog(self):
        assert discovery.format_tools_epilog({}) is None

    def test_epilog_lists_tools(self, tools_dir):
        (tools_dir / "a.py").write_text(tool_source("a-tool", "Does A"))
        (tools_dir / "b.py").write_text(tool_source("b-tool", "Does B"))
        epilog = discovery.format_tools_epilog(discovery.discover_tools())
        assert "a-tool" in epilog and "Does A" in epilog
        assert "b-tool" in epilog and "Does B" in epilog
        assert str(discovery.tools_dir()) in epilog
