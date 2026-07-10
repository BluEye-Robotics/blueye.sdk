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


class _StubChoice:
    def __init__(self, value, disabled=False):
        self.value = value
        self.disabled = disabled


class _StubControl:
    """Mimics questionary's InquirerControl selection state for the bulk helpers."""

    def __init__(self, visible, selected=()):
        self.filtered_choices = [_StubChoice(value) for value in visible]
        self.selected_options = list(selected)


class TestFilterScopedBulkActions:
    def test_toggle_all_selects_only_visible(self):
        from blueye.sdk.cli.prompts import _toggle_all_visible

        control = _StubControl(visible=["a", "b"], selected=["hidden"])
        _toggle_all_visible(control)
        assert sorted(control.selected_options) == ["a", "b", "hidden"]

    def test_toggle_all_deselects_when_all_visible_selected(self):
        from blueye.sdk.cli.prompts import _toggle_all_visible

        control = _StubControl(visible=["a", "b"], selected=["a", "b", "hidden"])
        _toggle_all_visible(control)
        assert control.selected_options == ["hidden"]

    def test_invert_only_touches_visible(self):
        from blueye.sdk.cli.prompts import _invert_visible

        control = _StubControl(visible=["a", "b"], selected=["a", "hidden"])
        _invert_visible(control)
        assert sorted(control.selected_options) == ["b", "hidden"]

    def test_disabled_choices_are_skipped(self):
        from blueye.sdk.cli.prompts import _toggle_all_visible

        control = _StubControl(visible=["a"])
        control.filtered_choices.append(_StubChoice("locked", disabled=True))
        _toggle_all_visible(control)
        assert control.selected_options == ["a"]

    def test_rebinding_attaches_to_real_prompt(self):
        """The workaround must find the control and replace both key bindings."""
        import questionary
        from prompt_toolkit.keys import Keys

        from blueye.sdk.cli.prompts import _scope_bulk_bindings_to_filter

        prompt = questionary.checkbox(
            "Pick:", choices=["a", "b"], use_search_filter=True, use_jk_keys=False
        )
        _scope_bulk_bindings_to_filter(prompt)
        bindings = prompt.application.key_bindings

        def exact(keys):
            # get_bindings_for_keys also returns the <any> search-character catch-all;
            # only the exact-key binding handles the shortcut at dispatch time.
            return [b for b in bindings.get_bindings_for_keys(keys) if b.keys == keys]

        toggle = exact((Keys.ControlA,))
        invert = exact((Keys.ControlI,))
        assert len(toggle) == 1 and toggle[0].handler.__name__ == "_toggle_all"
        assert len(invert) == 1 and invert[0].handler.__name__ == "_invert"
