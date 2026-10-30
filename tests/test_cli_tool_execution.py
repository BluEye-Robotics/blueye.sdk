import json
import os
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
        import the CLI's blueye.sdk), with the declared dependencies layered on top.
        Each requirement is a --with option; --with-requirements <script> needs
        uv 0.9 or newer."""
        tool = self._tool(tools_dir, dependencies=["nonexistent-package", "other>=1"])
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        # No per-user folder to forward, whatever the developer's own interpreter does
        mocker.patch("site.ENABLE_USER_SITE", False)
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        assert execution.run_tool(tool, ["-x"]) == 0
        assert run.call_args[0][0] == [
            "uv",
            "run",
            "--no-project",
            "--python",
            sys.executable,
            "--with",
            "nonexistent-package",
            "--with",
            "other>=1",
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


def write_wheel(path, name, version, module_source):
    """A minimal pure-Python wheel, built by hand so the test needs no network."""
    import base64
    import hashlib
    import zipfile

    dist_info = f"{name}-{version}.dist-info"
    files = {
        f"{name}.py": module_source,
        f"{dist_info}/METADATA": f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        f"{dist_info}/WHEEL": (
            "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n"
        ),
    }
    record = []
    with zipfile.ZipFile(path, "w") as wheel:
        for member, content in files.items():
            wheel.writestr(member, content)
            digest = hashlib.sha256(content.encode()).digest()
            encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
            record.append(f"{member},sha256={encoded},{len(content.encode())}")
        record.append(f"{dist_info}/RECORD,,")
        wheel.writestr(f"{dist_info}/RECORD", "\n".join(record) + "\n")
    return path


class TestUserSitePackages:
    """An SDK installed with ``pip install --user`` lives in the per-user folder, which uv's
    layered virtualenv does not read. When the CLI runs with the user site enabled, the
    tool is started through a bootstrap that adds the folder to the end of the search
    path, after uv's packages."""

    def _tool(self, tools_dir):
        write_tool(tools_dir, "uv-tool", "pass\n", dependencies=["other>=1"])
        return discovery.discover_tools()["uv-tool"]

    def _user_site(self, mocker, tmp_path, enabled=True, exists=True):
        user_site = tmp_path / "user-site"
        if exists:
            user_site.mkdir()
        mocker.patch("site.ENABLE_USER_SITE", enabled)
        mocker.patch("site.getusersitepackages", return_value=str(user_site))
        return str(user_site)

    def test_user_site_is_forwarded_through_the_bootstrap(self, tools_dir, tmp_path, mocker):
        user_site = self._user_site(mocker, tmp_path)
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        tool = self._tool(tools_dir)
        execution.run_tool(tool, ["--flag", "x"])
        command = run.call_args[0][0]
        assert command[:7] == [
            "uv",
            "run",
            "--no-project",
            "--python",
            sys.executable,
            "--with",
            "other>=1",
        ]
        assert command[7:] == [
            "python",
            "-c",
            execution._USER_SITE_BOOTSTRAP,
            user_site,
            str(tool.path),
            "--flag",
            "x",
        ]

    def test_script_runs_directly_inside_a_virtualenv(self, tools_dir, tmp_path, mocker):
        # Python disables the user site inside a virtualenv, and the CLI's venv is what uv
        # layers on, so there is nothing to add
        self._user_site(mocker, tmp_path, enabled=False)
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        tool = self._tool(tools_dir)
        execution.run_tool(tool, [])
        assert run.call_args[0][0][-2:] == ["python", str(tool.path)]

    def test_script_runs_directly_when_the_folder_does_not_exist(self, tools_dir, tmp_path, mocker):
        self._user_site(mocker, tmp_path, exists=False)
        mocker.patch("shutil.which", return_value="/usr/bin/uv")
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        tool = self._tool(tools_dir)
        execution.run_tool(tool, [])
        assert run.call_args[0][0][-2:] == ["python", str(tool.path)]

    def test_script_runs_directly_without_uv(self, tools_dir, tmp_path, mocker):
        # The plain interpreter reads the user site itself
        self._user_site(mocker, tmp_path)
        mocker.patch("shutil.which", return_value=None)
        run = mocker.patch("subprocess.run", return_value=mocker.Mock(returncode=0))
        tool = self._tool(tools_dir)
        execution.run_tool(tool, [])
        assert run.call_args[0][0] == [sys.executable, str(tool.path)]

    @pytest.mark.skipif(shutil.which("uv") is None, reason="uv is not installed")
    def test_overlay_wins_over_the_user_site_under_uv(self, tools_dir, tmp_path, mocker):
        """End-to-end with the real uv and a forced overlay. The tool's dependency is a
        handmade wheel the CLI's environment does not have, so uv builds an overlay for
        it, offline. The user site holds an older copy of the same module and a module
        that exists nowhere else. The tool must see uv's version and the user-site-only
        module, run as __main__ with its own argv, and import a sibling file."""
        user_site = tmp_path / "user-site"
        user_site.mkdir()
        (user_site / "only_in_overlay.py").write_text("VERSION = '1.0'\n")
        (user_site / "only_in_user_site.py").write_text("MARKER = 'found'\n")
        mocker.patch("site.ENABLE_USER_SITE", True)
        mocker.patch("site.getusersitepackages", return_value=str(user_site))
        wheel = write_wheel(
            tmp_path / "only_in_overlay-2.0-py3-none-any.whl",
            "only_in_overlay",
            "2.0",
            "VERSION = '2.0'\n",
        )
        (tools_dir / "sibling.py").write_text("X = 'sibling ok'\n")
        out_file = tmp_path / "result.json"
        write_tool(
            tools_dir,
            "overlay-tool",
            "import json, sys\n"
            "import blueye.sdk, only_in_overlay, only_in_user_site, sibling\n"
            "result = dict(name=__name__, argv=sys.argv[1:], overlay=only_in_overlay.VERSION,\n"
            "              user_site=only_in_user_site.MARKER, sibling=sibling.X)\n"
            f"open({str(out_file)!r}, 'w').write(json.dumps(result))\n"
            "sys.exit(7)\n",
            dependencies=[str(wheel)],
        )
        assert main(["overlay-tool", "--flag", "x"]) == 7
        assert json.loads(out_file.read_text()) == {
            "name": "__main__",
            "argv": ["--flag", "x"],
            "overlay": "2.0",
            "user_site": "found",
            "sibling": "sibling ok",
        }


class TestUserSiteBootstrap:
    """The bootstrap must behave like ``python script.py args`` for everything a tool can
    observe. It is run on the test interpreter directly, without uv, which is enough: uv
    only changes which interpreter runs it."""

    def _run(self, user_site, script, *args):
        import subprocess

        return subprocess.run(
            [
                sys.executable,
                "-c",
                execution._USER_SITE_BOOTSTRAP,
                str(user_site),
                str(script),
                *args,
            ],
            capture_output=True,
            text=True,
        )

    def test_module_globals_match_a_plain_run(self, tmp_path):
        user_site = tmp_path / "user-site"
        user_site.mkdir()
        tools = tmp_path / "tools"
        tools.mkdir()
        (tools / "sibling.py").write_text("X = 'sibling ok'\n")
        script = tools / "tool.py"
        script.write_text(
            "import json, os, sys\n"
            "import sibling\n"
            "print(json.dumps(dict(name=__name__, file=__file__, spec=__spec__, argv=sys.argv,\n"
            "      path0=sys.path[0], user_site_last=sys.path[-1], sibling=sibling.X)))\n"
        )
        result = self._run(user_site, os.path.relpath(script), "--flag", "x")
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {
            "name": "__main__",
            "file": str(script),
            "spec": None,
            "argv": [os.path.relpath(script), "--flag", "x"],
            "path0": str(tools),
            "user_site_last": str(user_site),
            "sibling": "sibling ok",
        }

    @pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
    def test_symlinked_tool_imports_siblings_of_its_target(self, tmp_path):
        user_site = tmp_path / "user-site"
        user_site.mkdir()
        real = tmp_path / "real"
        real.mkdir()
        (real / "sibling.py").write_text("X = 'sibling ok'\n")
        (real / "tool.py").write_text("import sibling\nprint(sibling.X)\n")
        link = tmp_path / "tool-link.py"
        link.symlink_to(real / "tool.py")
        result = self._run(user_site, link)
        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == "sibling ok"

    def test_script_stays_main_through_atexit_and_excepthook(self, tmp_path):
        user_site = tmp_path / "user-site"
        user_site.mkdir()
        script = tmp_path / "tool.py"
        script.write_text(
            "import atexit, sys\n"
            "MARKER = 'still main'\n"
            "atexit.register(lambda: print('atexit', __import__('__main__').MARKER))\n"
            "def hook(exc_type, exc, tb):\n"
            "    print('hook', exc_type.__name__, __import__('__main__').MARKER)\n"
            "sys.excepthook = hook\n"
            "raise ValueError('boom')\n"
        )
        result = self._run(user_site, script)
        assert result.returncode == 1
        assert result.stdout.splitlines() == ["hook ValueError still main", "atexit still main"]

    def test_exit_code_passes_through(self, tmp_path):
        user_site = tmp_path / "user-site"
        user_site.mkdir()
        script = tmp_path / "tool.py"
        script.write_text("import sys\nsys.exit(7)\n")
        assert self._run(user_site, script).returncode == 7


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
