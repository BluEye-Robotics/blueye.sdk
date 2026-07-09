import pytest

from blueye.sdk.cli.errors import CliError
from blueye.sdk.cli.prompts import NonInteractivePrompter


class TestNonInteractivePrompter:
    def test_select_returns_default(self):
        prompter = NonInteractivePrompter()
        assert prompter.select("Format?", ["a", "b"], "b", "--format") == "b"

    def test_select_without_default_names_the_flag(self):
        prompter = NonInteractivePrompter()
        with pytest.raises(CliError, match=r"--format"):
            prompter.select("Format?", ["a", "b"], None, "--format")

    def test_text_returns_default(self):
        prompter = NonInteractivePrompter()
        assert prompter.text("Name?", "model", "--name") == "model"

    def test_text_without_default_names_the_flag(self):
        prompter = NonInteractivePrompter()
        with pytest.raises(CliError, match=r"--anchors"):
            prompter.text("Anchors?", "", "--anchors")

    def test_confirm_returns_default(self):
        prompter = NonInteractivePrompter()
        assert prompter.confirm("Continue?", True, "--strict") is True
        assert prompter.confirm("Overwrite?", False, "--force") is False

    def test_path_without_default_names_the_flag(self):
        prompter = NonInteractivePrompter()
        with pytest.raises(CliError, match=r"--labels"):
            prompter.path("Labels file?", None, "--labels")


class TestDepsGuidance:
    def test_missing_deps_detection(self, mocker):
        from blueye.sdk.cli import deps

        find_spec = mocker.patch("importlib.util.find_spec")
        find_spec.side_effect = lambda name: None if name == "onnx" else object()
        assert deps.missing(("onnx", "rich", "questionary")) == ["onnx"]

    def test_guidance_prefers_uv_when_available(self, mocker, capsys):
        from blueye.sdk.cli import deps

        mocker.patch("shutil.which", return_value="/usr/local/bin/uv")
        deps.print_install_guidance(["onnx"])
        assert "uv pip install" in capsys.readouterr().out

    def test_guidance_falls_back_to_pip(self, mocker, capsys):
        from blueye.sdk.cli import deps

        mocker.patch("shutil.which", return_value=None)
        deps.print_install_guidance(["onnx"])
        assert "python -m pip install" in capsys.readouterr().out

    def test_guidance_mentions_powershell_on_windows(self, mocker, capsys):
        from blueye.sdk.cli import deps

        mocker.patch("shutil.which", return_value=None)
        mocker.patch("sys.platform", "win32")
        deps.print_install_guidance(["onnx"])
        assert "PowerShell" in capsys.readouterr().out

    def test_guidance_uses_single_quotes_with_uv_on_windows(self, mocker, capsys):
        from blueye.sdk.cli import deps

        mocker.patch("shutil.which", return_value="C:\\uv.exe")
        mocker.patch("sys.platform", "win32")
        deps.print_install_guidance(["onnx"])
        out = capsys.readouterr().out
        assert "uv pip install 'blueye.sdk[cli]'" in out
