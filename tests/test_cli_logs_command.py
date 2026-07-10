import pytest

from blueye.sdk.cli.main import main
from blueye.sdk.logs import LogFile


def make_log(name: str, start_time: int, filesize: int = 2048, is_dive: bool = True) -> LogFile:
    return LogFile(
        name=name,
        is_dive=is_dive,
        filesize=filesize,
        start_time=start_time,
        max_depth_magnitude=20,
        ip="192.168.1.101",
    )


@pytest.fixture
def drone(mocker, monkeypatch):
    """Mocked Drone with two real LogFile objects; download patched out."""
    monkeypatch.setenv("COLUMNS", "200")
    logs = [
        make_log("BYEDP000000_aaaa_00000", start_time=1700000000),
        make_log("BYEDP000000_aaaa_00001", start_time=1700100000, is_dive=False),
    ]
    mocker.patch.object(LogFile, "download", autospec=True, return_value=b"")
    drone_cls = mocker.patch("blueye.sdk.Drone", autospec=True)
    instance = drone_cls.return_value
    instance.logs = logs  # `list(drone.logs)` works on a plain list.
    instance._logs = {log.name: log for log in logs}
    instance._drone_cls = drone_cls
    return instance


class TestList:
    def test_list_renders_table(self, drone, capsys):
        assert main(["logs", "list"]) == 0
        out = capsys.readouterr().out
        assert "BYEDP000000_aaaa_00000" in out
        assert "20 m" in out
        assert "2.0 KiB" in out
        assert "yes" in out and "no" in out

    def test_connects_as_observer_and_disconnects(self, drone):
        assert main(["logs", "list"]) == 0
        kwargs = drone._drone_cls.call_args.kwargs
        assert kwargs["connect_as_observer"] is True
        assert kwargs["ip"] == "192.168.1.101"
        drone.disconnect.assert_called_once()

    def test_drone_ip_flag(self, drone):
        assert main(["logs", "list", "--drone-ip", "192.168.1.42"]) == 0
        assert drone._drone_cls.call_args.kwargs["ip"] == "192.168.1.42"

    def test_empty_logs(self, drone, capsys):
        drone.logs = []
        assert main(["logs", "list"]) == 0
        assert "No logs" in capsys.readouterr().out

    def test_bare_invocation_without_tty_lists(self, drone, mocker, capsys):
        mocker.patch("sys.stdin.isatty", return_value=False)
        assert main(["logs"]) == 0
        assert "BYEDP000000_aaaa_00000" in capsys.readouterr().out


class TestDownload:
    def test_download_by_name(self, drone, tmp_path):
        assert main(["logs", "download", "BYEDP000000_aaaa_00000", "-o", str(tmp_path)]) == 0
        LogFile.download.assert_called_once()
        call = LogFile.download.call_args
        assert call.args[0].name == "BYEDP000000_aaaa_00000"
        assert call.kwargs["output_path"] == tmp_path

    def test_unknown_name_lists_available(self, drone, capsys):
        assert main(["logs", "download", "nope"]) == 1
        err = capsys.readouterr().err
        assert "No log named nope" in err
        assert "BYEDP000000_aaaa_00000" in err

    def test_latest_picks_newest(self, drone, tmp_path):
        assert main(["logs", "download", "--latest", "1", "-o", str(tmp_path)]) == 0
        call = LogFile.download.call_args
        assert call.args[0].name == "BYEDP000000_aaaa_00001"  # newer start_time

    def test_all_downloads_everything(self, drone, tmp_path):
        assert main(["logs", "download", "--all", "-o", str(tmp_path)]) == 0
        assert LogFile.download.call_count == 2

    def test_no_selector_errors(self, drone, capsys):
        assert main(["logs", "download"]) == 1
        assert "--latest" in capsys.readouterr().err


class TestFailureHandling:
    def test_unreachable_drone_is_friendly(self, drone, capsys):
        drone._drone_cls.side_effect = ConnectionError("Could not establish connection with drone")
        assert main(["logs", "list"]) == 1
        err = capsys.readouterr().err
        assert "Could not reach the drone" in err
        assert "Traceback" not in err

    def test_logs_command_needs_no_onnx(self, drone, mocker):
        def fake_missing(names):
            return [name for name in names if name == "onnx"]

        mocker.patch("blueye.sdk.cli.deps.missing", side_effect=fake_missing)
        assert main(["logs", "list"]) == 0


class TestInteractive:
    def test_interactive_checkbox_download(self, drone, mocker, tmp_path):
        class FakePrompter:
            def checkbox(self, question, choices, flag):
                return [choices[0]]  # Select the first log.

            def text(self, question, default, flag):
                return str(tmp_path)

        mocker.patch("sys.stdin.isatty", return_value=True)
        mocker.patch("sys.stdout.isatty", return_value=True)
        mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=FakePrompter())

        assert main(["logs"]) == 0
        LogFile.download.assert_called_once()
        assert LogFile.download.call_args.kwargs["output_path"] == tmp_path

    def test_interactive_empty_selection(self, drone, mocker, capsys):
        class FakePrompter:
            def checkbox(self, question, choices, flag):
                return []

        mocker.patch("sys.stdin.isatty", return_value=True)
        mocker.patch("sys.stdout.isatty", return_value=True)
        mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=FakePrompter())

        assert main(["logs"]) == 0
        LogFile.download.assert_not_called()
        assert "Nothing selected" in capsys.readouterr().out
