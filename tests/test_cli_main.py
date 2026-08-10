import json
import zipfile

import onnx
import onnx.helper
import pytest

from blueye.sdk.cli import main as cli_main_module
from blueye.sdk.cli.errors import CliError
from blueye.sdk.cli.main import main


class FakePrompter:
    """Prompter that records questions and answers from a canned dict."""

    def __init__(self, answers=None):
        self.answers = answers or {}
        self.questions = []

    def _answer(self, question, default):
        self.questions.append(question)
        for fragment, answer in self.answers.items():
            if fragment in question:
                return answer
        return default

    def select(self, question, choices, default, flag):
        answer = self._answer(question, default)
        if answer is None:
            raise CliError(f"no answer for: {question}")
        return answer

    def text(self, question, default, flag):
        return self._answer(question, default)

    def confirm(self, question, default, flag):
        return self._answer(question, default)

    def path(self, question, default, flag):
        answer = self._answer(question, default)
        if answer is None:
            raise CliError(f"no answer for: {question}")
        return answer


@pytest.fixture
def fake_prompter(mocker):
    prompter = FakePrompter()
    mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=prompter)
    mocker.patch("blueye.sdk.cli.prompts.NonInteractivePrompter", return_value=prompter)
    return prompter


@pytest.fixture
def yolov8_model(tmp_path):
    """A tiny model whose shapes and metadata mimic an Ultralytics YOLOv8 export."""
    images = onnx.helper.make_tensor_value_info("images", onnx.TensorProto.FLOAT, [1, 3, 640, 640])
    output0 = onnx.helper.make_tensor_value_info("output0", onnx.TensorProto.FLOAT, [1, 84, 8400])
    node = onnx.helper.make_node("Identity", ["images"], ["output0"])
    graph = onnx.helper.make_graph([node], "g", [images], [output0])
    model = onnx.helper.make_model(graph)
    names = "{" + ", ".join(f"{i}: 'class{i}'" for i in range(80)) + "}"
    onnx.helper.set_model_props(model, {"names": names, "imgsz": "[640, 640]", "task": "detect"})
    path = tmp_path / "yolov8n.onnx"
    onnx.save(model, str(path))
    return path


def test_help_exits_zero():
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def test_no_command_prints_help(capsys):
    assert main([]) == 0
    assert "bundle-model" in capsys.readouterr().out


def test_missing_deps_prints_guidance(mocker, capsys):
    mocker.patch("blueye.sdk.cli.deps.missing", return_value=["onnx"])
    exit_code = main(["bundle-model", "whatever.onnx"])
    assert exit_code == 2
    output = capsys.readouterr().out
    assert "blueye.sdk[cli]" in output
    assert "onnx" in output


def test_bundle_end_to_end(yolov8_model, fake_prompter, tmp_path):
    output = tmp_path / "bundle.zip"
    exit_code = main(
        ["bundle-model", str(yolov8_model), "--yes", "--name", "Test YOLO", "-o", str(output)]
    )
    assert exit_code == 0
    with zipfile.ZipFile(output) as archive:
        assert sorted(archive.namelist()) == ["model.onnx", "model_meta.json"]
        meta = json.loads(archive.read("model_meta.json"))
    assert meta["name"] == "Test YOLO"
    assert meta["detection"]["output_format"] == "yolov8_flat"
    assert meta["detection"]["num_classes"] == 80
    assert meta["detection"]["input_width"] == 640
    assert len(meta["labels"]) == 80
    # Packages default to autolaunching on the drone.
    assert meta["runtime"]["enabled"] is True


def test_dry_run_writes_nothing(yolov8_model, fake_prompter, tmp_path, capsys):
    output = tmp_path / "bundle.zip"
    exit_code = main(["bundle-model", str(yolov8_model), "--yes", "--dry-run", "-o", str(output)])
    assert exit_code == 0
    assert not output.exists()
    assert "yolov8_flat" in capsys.readouterr().out


def test_existing_output_without_force_fails(yolov8_model, tmp_path, mocker):
    from blueye.sdk.cli.prompts import NonInteractivePrompter

    output = tmp_path / "bundle.zip"
    output.write_bytes(b"existing")
    # Real NonInteractivePrompter: confirm() returns its default, which is False when
    # --yes was not passed (non-TTY path).
    mocker.patch("sys.stdin.isatty", return_value=False)
    exit_code = main(["bundle-model", str(yolov8_model), "-o", str(output)])
    assert exit_code == 1
    assert output.read_bytes() == b"existing"


def test_force_overwrites(yolov8_model, fake_prompter, tmp_path):
    output = tmp_path / "bundle.zip"
    output.write_bytes(b"existing")
    exit_code = main(["bundle-model", str(yolov8_model), "--yes", "--force", "-o", str(output)])
    assert exit_code == 0
    assert zipfile.is_zipfile(output)


def test_unsupported_classifier_errors_cleanly(tmp_path, fake_prompter, capsys):
    images = onnx.helper.make_tensor_value_info("images", onnx.TensorProto.FLOAT, [1, 3, 224, 224])
    probs = onnx.helper.make_tensor_value_info("probs", onnx.TensorProto.FLOAT, [1, 1000])
    node = onnx.helper.make_node("Identity", ["images"], ["probs"])
    graph = onnx.helper.make_graph([node], "g", [images], [probs])
    path = tmp_path / "classifier.onnx"
    onnx.save(onnx.helper.make_model(graph), str(path))

    exit_code = main(["bundle-model", str(path), "--yes"])
    assert exit_code == 1
    assert "classifier" in capsys.readouterr().out


def test_not_an_onnx_file_errors_cleanly(tmp_path, fake_prompter, capsys):
    path = tmp_path / "junk.onnx"
    path.write_bytes(b"garbage")
    exit_code = main(["bundle-model", str(path), "--yes"])
    assert exit_code == 1
    assert "Not a valid ONNX model" in capsys.readouterr().out


def test_runtime_flags_flow_into_meta(yolov8_model, fake_prompter, tmp_path):
    output = tmp_path / "bundle.zip"
    exit_code = main(
        [
            "bundle-model",
            str(yolov8_model),
            "--yes",
            "-o",
            str(output),
            "--runtime-device",
            "tensorrt-dla1",
            "--runtime-hz",
            "10",
            "--runtime-enabled",
            "--tracking",
            "byte_track",
        ]
    )
    assert exit_code == 0
    with zipfile.ZipFile(output) as archive:
        meta = json.loads(archive.read("model_meta.json"))
    assert meta["runtime"] == {"enabled": True, "device": "tensorrt-dla1", "hz": 10.0}
    assert meta["tracking"]["algorithm"] == "byte_track"


def test_no_runtime_enabled_flag_disables_autolaunch(yolov8_model, fake_prompter, tmp_path):
    output = tmp_path / "bundle.zip"
    exit_code = main(
        ["bundle-model", str(yolov8_model), "--yes", "-o", str(output), "--no-runtime-enabled"]
    )
    assert exit_code == 0
    with zipfile.ZipFile(output) as archive:
        meta = json.loads(archive.read("model_meta.json"))
    assert meta["runtime"]["enabled"] is False


def test_runtime_hz_max_is_unlimited(yolov8_model, fake_prompter, tmp_path):
    output = tmp_path / "bundle.zip"
    main(
        [
            "bundle-model",
            str(yolov8_model),
            "--yes",
            "-o",
            str(output),
            "--runtime-device",
            "cuda",
            "--runtime-hz",
            "max",
        ]
    )
    with zipfile.ZipFile(output) as archive:
        meta = json.loads(archive.read("model_meta.json"))
    assert "hz" not in meta["runtime"]


def test_labels_file_flag(yolov8_model, fake_prompter, tmp_path):
    labels_file = tmp_path / "labels.txt"
    labels_file.write_text("\n".join(f"label{i}" for i in range(80)))
    output = tmp_path / "bundle.zip"
    exit_code = main(
        [
            "bundle-model",
            str(yolov8_model),
            "--yes",
            "-o",
            str(output),
            "--labels",
            str(labels_file),
        ]
    )
    assert exit_code == 0
    with zipfile.ZipFile(output) as archive:
        meta = json.loads(archive.read("model_meta.json"))
    assert meta["labels"][0] == "label0"


def test_cli_module_importable_without_optional_deps(mocker):
    """The dependency gate must run before any optional import."""
    # Simulate the extra being missing; parsing + gate must still work.
    mocker.patch("blueye.sdk.cli.deps.missing", return_value=["rich", "questionary"])
    assert main(["bundle-model", "x.onnx"]) == 2


class TestReviewRegressions:
    """Regression tests for the PR review findings: user input errors must exit
    cleanly, never with a traceback."""

    def test_bad_anchor_values_error_cleanly(self, yolov8_model, fake_prompter, capsys):
        # --anchors is only consumed on the yolov2_grid path, so force the format.
        exit_code = main(
            [
                "bundle-model",
                str(yolov8_model),
                "--yes",
                "--format",
                "yolov2_grid",
                "--grid-size",
                "13",
                "--anchors",
                "1.0,abc",
                "--dry-run",
            ]
        )
        assert exit_code == 1
        assert "numbers" in capsys.readouterr().err

    def test_bad_runtime_hz_flag_errors_cleanly(self, yolov8_model, fake_prompter, capsys):
        exit_code = main(
            ["bundle-model", str(yolov8_model), "--yes", "--runtime-hz", "fast", "--dry-run"]
        )
        assert exit_code == 1
        assert "must be a number" in capsys.readouterr().err

    def test_bad_custom_rate_answer_errors_cleanly(self, yolov8_model, fake_prompter, capsys):
        fake_prompter.answers["Maximum inference rate?"] = "custom..."
        fake_prompter.answers["Rate in Hz"] = "warp-speed"
        exit_code = main(["bundle-model", str(yolov8_model), "--yes", "--dry-run"])
        assert exit_code == 1
        assert "must be a number" in capsys.readouterr().err

    def test_yes_without_force_does_not_overwrite(
        self, yolov8_model, fake_prompter, tmp_path, capsys
    ):
        output = tmp_path / "bundle.zip"
        output.write_bytes(b"existing")
        exit_code = main(["bundle-model", str(yolov8_model), "--yes", "-o", str(output)])
        assert exit_code == 1
        assert output.read_bytes() == b"existing"
        assert "--force" in capsys.readouterr().err


class TestPushToDrone:
    @pytest.fixture
    def mocked_drone_upload(self, mocker):
        from blueye.sdk.cv_models import CvModel

        client = mocker.Mock()
        client.upload.return_value = CvModel(
            name="Test YOLO",
            directory="test-yolo",
            type="detection",
            output_format="yolov8_flat",
            size_bytes=1,
            labels=["x"],
            enabled=True,
            raw={},
        )
        drone_cls = mocker.patch("blueye.sdk.Drone", autospec=True)
        drone_cls.return_value.cv_models = client
        client._drone_cls = drone_cls
        return client

    def test_push_uploads_and_reports(
        self, yolov8_model, fake_prompter, mocked_drone_upload, tmp_path, capsys
    ):
        output = tmp_path / "bundle.zip"
        exit_code = main(["bundle-model", str(yolov8_model), "--yes", "-o", str(output), "--push"])
        assert exit_code == 0
        mocked_drone_upload.upload.assert_called_once_with(output)
        out = capsys.readouterr().out
        assert "test-yolo" in out

    def test_drone_ip_flag_reaches_constructor(
        self, yolov8_model, fake_prompter, mocked_drone_upload, tmp_path
    ):
        output = tmp_path / "bundle.zip"
        main(
            [
                "bundle-model",
                str(yolov8_model),
                "--yes",
                "-o",
                str(output),
                "--push",
                "--drone-ip",
                "192.168.1.42",
            ]
        )
        assert mocked_drone_upload._drone_cls.call_args.kwargs["ip"] == "192.168.1.42"

    def test_unreachable_drone_fails_gracefully_keeping_bundle(
        self, yolov8_model, fake_prompter, mocked_drone_upload, tmp_path, capsys
    ):
        import requests

        mocked_drone_upload.upload.side_effect = requests.exceptions.ConnectionError("refused")
        output = tmp_path / "bundle.zip"
        exit_code = main(["bundle-model", str(yolov8_model), "--yes", "-o", str(output), "--push"])
        assert exit_code == 1
        assert zipfile.is_zipfile(output)  # The bundle itself was written.
        err = capsys.readouterr().err
        assert "Could not reach the drone" in err
        assert str(output) in err

    def test_drone_rejection_surfaces_reason(
        self, yolov8_model, fake_prompter, mocked_drone_upload, tmp_path, capsys
    ):
        import requests

        mocked_drone_upload.upload.side_effect = requests.exceptions.HTTPError(
            "400 error: model_meta.json not found in zip archive."
        )
        output = tmp_path / "bundle.zip"
        exit_code = main(["bundle-model", str(yolov8_model), "--yes", "-o", str(output), "--push"])
        assert exit_code == 1
        assert "rejected" in capsys.readouterr().err

    def test_yes_without_push_does_not_upload(
        self, yolov8_model, fake_prompter, mocked_drone_upload, tmp_path
    ):
        output = tmp_path / "bundle.zip"
        assert main(["bundle-model", str(yolov8_model), "--yes", "-o", str(output)]) == 0
        mocked_drone_upload.upload.assert_not_called()
