import pytest
import requests

from blueye.sdk.cli.main import main
from blueye.sdk.cv_models import CvModel

MODEL = CvModel(
    name="Cod Detector",
    directory="cod-detector",
    type="detection",
    output_format="yolov8_flat",
    size_bytes=10 * 1024 * 1024,
    labels=["cod"],
    enabled=False,
    raw={"runtime": {"device": "tensorrt-dla0", "hz": 10, "enabled": False}},
)


@pytest.fixture
def cv_models(mocker, monkeypatch):
    """Mock the CvModels client the command builds, capturing the Drone ctor args."""
    monkeypatch.setenv("COLUMNS", "200")  # Keep rich from wrapping table cells.
    client = mocker.Mock()
    client.list.return_value = [MODEL]
    client.upload.return_value = MODEL
    drone_cls = mocker.patch("blueye.sdk.Drone", autospec=True)
    drone_cls.return_value.cv_models = client
    client._drone_cls = drone_cls
    return client


class TestList:
    def test_list_renders_table(self, cv_models, capsys):
        assert main(["models", "list"]) == 0
        out = capsys.readouterr().out
        assert "Cod Detector" in out
        assert "cod-detector" in out
        assert "yolov8_flat" in out
        assert "tensorrt-dla0" in out
        assert "10" in out

    def test_drone_ip_flag_reaches_constructor(self, cv_models):
        assert main(["models", "list", "--drone-ip", "192.168.1.42"]) == 0
        assert cv_models._drone_cls.call_args.kwargs["ip"] == "192.168.1.42"

    def test_empty_list(self, cv_models, capsys):
        cv_models.list.return_value = []
        assert main(["models", "list"]) == 0
        assert "No CV models" in capsys.readouterr().out

    def test_bare_invocation_without_tty_lists(self, cv_models, mocker, capsys):
        mocker.patch("sys.stdin.isatty", return_value=False)
        assert main(["models"]) == 0
        assert "cod-detector" in capsys.readouterr().out


class TestActions:
    def test_enable(self, cv_models):
        assert main(["models", "enable", "cod-detector"]) == 0
        cv_models.set_enabled.assert_called_once_with("cod-detector", True, timeout=5.0)

    def test_disable(self, cv_models):
        assert main(["models", "disable", "cod-detector"]) == 0
        cv_models.set_enabled.assert_called_once_with("cod-detector", False, timeout=5.0)

    def test_set_device(self, cv_models):
        assert main(["models", "set-device", "cod-detector", "tensorrt-dla1"]) == 0
        cv_models.set_device.assert_called_once_with("cod-detector", "tensorrt-dla1", timeout=5.0)

    def test_set_device_rejects_unknown_choice(self, cv_models):
        with pytest.raises(SystemExit):
            main(["models", "set-device", "cod-detector", "gameboy"])

    def test_set_hz(self, cv_models):
        assert main(["models", "set-hz", "cod-detector", "10"]) == 0
        cv_models.set_hz.assert_called_once_with("cod-detector", 10, timeout=5.0)

    def test_warmup(self, cv_models):
        assert main(["models", "warmup", "cod-detector"]) == 0
        cv_models.warmup.assert_called_once_with("cod-detector")

    def test_rescan(self, cv_models):
        assert main(["models", "rescan"]) == 0
        cv_models.rescan.assert_called_once()

    def test_upload(self, cv_models, tmp_path, capsys):
        package = tmp_path / "pkg.zip"
        package.write_bytes(b"zip")
        assert main(["models", "upload", str(package)]) == 0
        cv_models.upload.assert_called_once()
        assert "cod-detector" in capsys.readouterr().out

    def test_upload_missing_file(self, cv_models, tmp_path, capsys):
        assert main(["models", "upload", str(tmp_path / "nope.zip")]) == 1
        assert "No such file" in capsys.readouterr().err

    def test_download(self, cv_models, tmp_path, capsys):
        cv_models.download.return_value = tmp_path / "cod-detector.zip"
        assert main(["models", "download", "cod-detector", "-o", str(tmp_path)]) == 0
        cv_models.download.assert_called_once_with("cod-detector", output_path=tmp_path)


class TestDelete:
    def test_delete_with_force(self, cv_models):
        assert main(["models", "delete", "cod-detector", "--force"]) == 0
        cv_models.delete.assert_called_once_with("cod-detector", timeout=5.0)

    def test_delete_without_force_non_interactive_fails(self, cv_models, mocker, capsys):
        mocker.patch("sys.stdin.isatty", return_value=False)
        assert main(["models", "delete", "cod-detector"]) == 1
        cv_models.delete.assert_not_called()
        assert "--force" in capsys.readouterr().err


class TestFailureHandling:
    def test_unreachable_drone_is_friendly(self, cv_models, capsys):
        cv_models.list.side_effect = requests.exceptions.ConnectionError("refused")
        assert main(["models", "list"]) == 1
        err = capsys.readouterr().err
        assert "Could not reach the drone" in err
        assert "Traceback" not in err

    def test_server_reason_surfaces(self, cv_models, capsys):
        cv_models.set_device.side_effect = requests.exceptions.HTTPError(
            "400 error: 'device' must be one of: cuda, tensorrt."
        )
        assert main(["models", "set-device", "cod-detector", "cuda"]) == 1
        assert "must be one of" in capsys.readouterr().err

    def test_models_command_needs_no_onnx(self, cv_models, mocker):
        def fake_missing(names):
            return [name for name in names if name == "onnx"]

        mocker.patch("blueye.sdk.cli.deps.missing", side_effect=fake_missing)
        assert main(["models", "list"]) == 0


class TestInteractive:
    def test_interactive_toggle_flow(self, cv_models, mocker):
        """Select the model, toggle autolaunch, then quit."""
        answers = iter(
            [
                "cod-detector (disabled, tensorrt-dla0)",  # model select
                "Enable autolaunch",  # action select
                "Quit",  # second round: quit
            ]
        )

        class FakePrompter:
            def select(self, question, choices, default, flag):
                return next(answers)

            def confirm(self, question, default, flag):
                return default

        mocker.patch("sys.stdin.isatty", return_value=True)
        mocker.patch("sys.stdout.isatty", return_value=True)
        mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=FakePrompter())

        assert main(["models"]) == 0
        cv_models.set_enabled.assert_called_once_with("cod-detector", True, timeout=5.0)
