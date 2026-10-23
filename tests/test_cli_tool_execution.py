import json
import shutil
import sys

import pytest

from blueye.sdk.cli.external import discovery, execution
from blueye.sdk.cli.main import main


@pytest.fixture
def tools_dir(tmp_path, monkeypatch):
    directory = tmp_path / "cli-tools"
    directory.mkdir()
    monkeypatch.setenv(discovery.TOOLS_DIR_ENV, str(directory))
    return directory


def write_tool(tools_dir, name, body, dependencies=False):
    deps_line = '# dependencies = ["nonexistent-package"]\n' if dependencies is True else ""
    if isinstance(dependencies, list):
        deps_line = f"# dependencies = {json.dumps(dependencies)}\n"
    (tools_dir / f"{name}.py").write_text(
        "# /// script\n"
        + deps_line
        + "#\n# [tool.blueye]\n"
        + f'# name = "{name}"\n'
        + f'# description = "Test tool {name}"\n'
        + "# ///\n"
        + body
    )


class TestDispatch:
    def test_args_passed_verbatim(self, tools_dir, tmp_path):
        """The REMAINDER regression guard: leading-dash args reach the tool."""
        out_file = tmp_path / "argv.json"
        write_tool(
            tools_dir,
            "dump-args",
            f"import json, sys\nopen({str(out_file)!r}, 'w').write(json.dumps(sys.argv[1:]))\n",
        )
        exit_code = main(["dump-args", "--flag", "x", "-v", "positional"])
        assert exit_code == 0
        assert json.loads(out_file.read_text()) == ["--flag", "x", "-v", "positional"]

    def test_exit_code_propagated(self, tools_dir):
        write_tool(tools_dir, "fail-tool", "import sys\nsys.exit(7)\n")
        assert main(["fail-tool"]) == 7

    def test_builtin_wins_name_collision(self, tools_dir, tmp_path):
        marker = tmp_path / "ran.txt"
        write_tool(tools_dir, "tools", f"open({str(marker)!r}, 'w').write('ran')\n")
        # `blueye tools list` must run the built-in, not the tool.
        assert main(["tools", "list"]) == 0
        assert not marker.exists()

    def test_unknown_name_still_errors(self, tools_dir, capsys):
        with pytest.raises(SystemExit) as excinfo:
            main(["no-such-command"])
        assert excinfo.value.code == 2  # argparse's invalid-choice exit

    def test_tool_shown_in_help_epilog(self, tools_dir, capsys):
        write_tool(tools_dir, "depth-log", "pass\n")
        main([])
        out = capsys.readouterr().out
        assert "external tools" in out
        assert "depth-log" in out
        assert "Test tool depth-log" in out


class TestUvPreference:
    def _tool(self, tools_dir, dependencies):
        write_tool(tools_dir, "uv-tool", "pass\n", dependencies=dependencies)
        return discovery.discover_tools()["uv-tool"]

    def test_uv_layers_dependencies_on_the_cli_interpreter(self, tools_dir, mocker):
        """Regression guard for #270: the tool must run on sys.executable (so it can
        import the CLI's blueye.sdk), with the declared dependencies layered on top."""
        tool = self._tool(tools_dir, dependencies=True)
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        assert execution.run_tool(tool, ["-x"]) == 0
        assert run.call_args[0][0] == [
            "uv",
            "run",
            "--no-project",
            "--python",
            sys.executable,
            "--with-requirements",
            str(tool.path),
            "python",
            str(tool.path),
            "-x",
        ]

    def test_interpreter_used_without_uv(self, tools_dir, mocker):
        tool = self._tool(tools_dir, dependencies=True)
        mocker.patch("shutil.which", return_value=None)
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        execution.run_tool(tool, [])
        assert run.call_args[0][0] == [sys.executable, str(tool.path)]

    def test_interpreter_used_without_dependencies(self, tools_dir, mocker):
        tool = self._tool(tools_dir, dependencies=False)
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        execution.run_tool(tool, [])
        assert run.call_args[0][0] == [sys.executable, str(tool.path)]

    @pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")
    def test_tool_with_dependencies_imports_the_sdk_under_uv(self, tools_dir, tmp_path):
        """End-to-end #270 check with the real uv. The declared dependency is one the
        SDK already pulls in, so the run needs no network."""
        out_file = tmp_path / "sdk.json"
        write_tool(
            tools_dir,
            "sdk-tool",
            "import json, sys\n"
            "import blueye.sdk, tabulate\n"
            f"open({str(out_file)!r}, 'w').write(json.dumps(sys.argv[1:]))\n",
            dependencies=["tabulate"],
        )
        assert main(["sdk-tool", "--flag", "x"]) == 0
        assert json.loads(out_file.read_text()) == ["--flag", "x"]


class TestMinSdkVersionWarning:
    def test_newer_requirement_warns_but_runs(self, tools_dir, mocker, capsys):
        (tools_dir / "future.py").write_text(
            "# /// script\n# [tool.blueye]\n"
            '# name = "future-tool"\n# description = "Needs the future"\n'
            '# min-sdk-version = "999.0.0"\n# ///\npass\n'
        )
        tool = discovery.discover_tools()["future-tool"]
        mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        assert execution.run_tool(tool, []) == 0
        assert "999.0.0" in capsys.readouterr().err
