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
    def test_interactive_checkbox_download(self, drone, mocker, tmp_path, capsys):
        seen_choices = []

        class FakePrompter:
            def checkbox(self, question, choices, flag):
                seen_choices.extend(choices)
                return [choices[0]]  # Select the first (newest) log.

            def text(self, question, default, flag):
                return str(tmp_path)

            def confirm(self, question, default, flag):
                return default  # Decline the .mcap conversion.

        mocker.patch("sys.stdin.isatty", return_value=True)
        mocker.patch("sys.stdout.isatty", return_value=True)
        mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=FakePrompter())

        assert main(["logs"]) == 0
        LogFile.download.assert_called_once()
        assert LogFile.download.call_args.kwargs["output_path"] == tmp_path
        # Sorted descending alphabetically: _00001 before _00000.
        assert "BYEDP000000_aaaa_00001" in seen_choices[0]
        assert "BYEDP000000_aaaa_00000" in seen_choices[1]
        # The choices themselves are the table rows (name + time + size columns).
        assert "KiB" in seen_choices[0]
        # No duplicated full table before the picker — only the header line.
        out = capsys.readouterr().out
        assert "MAX DEPTH" not in out
        assert "NAME" in out

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


class TestMcapConversion:
    @pytest.fixture
    def bez_file(self, tmp_path):
        """A tiny real .bez (uncompressed binlog records) built with protobuf."""
        import blueye.protocol as bp

        from tests.test_logs import create_real_binlog_record

        records = b""
        for seconds in (100, 101, 102):
            payload = bp.DepthTel(depth=bp.Depth(value=float(seconds)))
            records += create_real_binlog_record(1700000000 + seconds, seconds, payload)
        path = tmp_path / "dive.bez"
        path.write_bytes(records)
        return path

    def test_convert_writes_valid_mcap(self, bez_file, tmp_path):
        from blueye.sdk.cli.commands.logs.mcap import convert_bez_to_mcap

        mcap_path = tmp_path / "dive.mcap"
        count = convert_bez_to_mcap(bez_file, mcap_path)
        assert count == 3
        content = mcap_path.read_bytes()
        assert content.startswith(b"\x89MCAP")  # MCAP magic bytes.
        assert len(content) > 100

    def test_convert_empty_log_errors(self, tmp_path):
        from blueye.sdk.cli.commands.logs.mcap import convert_bez_to_mcap
        from blueye.sdk.cli.errors import CliError

        empty = tmp_path / "empty.bez"
        empty.write_bytes(b"")
        with pytest.raises(CliError, match="no readable log records"):
            convert_bez_to_mcap(empty, tmp_path / "empty.mcap")

    def test_download_mcap_flag_converts(self, drone, mocker, tmp_path):
        convert = mocker.patch(
            "blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap", return_value=5
        )
        assert (
            main(
                [
                    "logs",
                    "download",
                    "BYEDP000000_aaaa_00000",
                    "-o",
                    str(tmp_path),
                    "--mcap",
                ]
            )
            == 0
        )
        convert.assert_called_once_with(
            tmp_path / "BYEDP000000_aaaa_00000.bez", tmp_path / "BYEDP000000_aaaa_00000.mcap"
        )

    def test_download_without_mcap_flag_does_not_convert(self, drone, mocker, tmp_path):
        convert = mocker.patch("blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap")
        assert main(["logs", "download", "--all", "-o", str(tmp_path)]) == 0
        convert.assert_not_called()

    def test_missing_mcap_dependency_gives_guidance(self, drone, mocker, tmp_path, capsys):
        def fake_missing(names):
            return [name for name in names if name == "mcap_protobuf"]

        mocker.patch("blueye.sdk.cli.deps.missing", side_effect=fake_missing)
        exit_code = main(["logs", "download", "--all", "-o", str(tmp_path), "--mcap"])
        assert exit_code == 1
        captured = capsys.readouterr()
        assert "blueye.sdk[cli]" in captured.out
        assert "mcap" in captured.err

    def test_interactive_offers_mcap_conversion(self, drone, mocker, tmp_path):
        convert = mocker.patch(
            "blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap", return_value=5
        )

        class FakePrompter:
            def checkbox(self, question, choices, flag):
                return [choices[0]]

            def text(self, question, default, flag):
                return str(tmp_path)

            def confirm(self, question, default, flag):
                return "mcap" in question  # Say yes to the conversion confirm.

        mocker.patch("sys.stdin.isatty", return_value=True)
        mocker.patch("sys.stdout.isatty", return_value=True)
        mocker.patch("blueye.sdk.cli.prompts.QuestionaryPrompter", return_value=FakePrompter())

        assert main(["logs"]) == 0
        convert.assert_called_once()


class TestFilters:
    def test_dives_only(self, drone, capsys):
        assert main(["logs", "list", "--dives-only"]) == 0
        out = capsys.readouterr().out
        assert "BYEDP000000_aaaa_00000" in out  # is_dive=True
        assert "BYEDP000000_aaaa_00001" not in out  # is_dive=False

    def test_since_filters_older_logs(self, drone, capsys):
        # Log _00001 starts at 1700100000 (~2023-11-16); _00000 at 1700000000 (~11-14).
        assert main(["logs", "list", "--since", "2023-11-16"]) == 0
        out = capsys.readouterr().out
        assert "BYEDP000000_aaaa_00001" in out
        assert "BYEDP000000_aaaa_00000" not in out

    def test_until_filters_newer_logs(self, drone, capsys):
        assert main(["logs", "list", "--until", "2023-11-15"]) == 0
        out = capsys.readouterr().out
        assert "BYEDP000000_aaaa_00000" in out
        assert "BYEDP000000_aaaa_00001" not in out

    def test_bad_date_errors_cleanly(self, drone, capsys):
        assert main(["logs", "list", "--since", "tomorrow"]) == 1
        err = capsys.readouterr().err
        assert "--since must be a date" in err  # The message names the expected format.

    def test_filters_apply_to_download_all(self, drone, tmp_path):
        assert main(["logs", "download", "--all", "--dives-only", "-o", str(tmp_path)]) == 0
        assert LogFile.download.call_count == 1

    def test_no_match_message(self, drone, capsys):
        assert main(["logs", "list", "--since", "2030-01-01"]) == 0
        assert "No logs match the filters" in capsys.readouterr().out


class TestSorting:
    def test_list_sorted_descending(self, drone, capsys):
        assert main(["logs", "list"]) == 0
        out = capsys.readouterr().out
        assert out.index("BYEDP000000_aaaa_00001") < out.index("BYEDP000000_aaaa_00000")


class TestConvert:
    @pytest.fixture
    def bez_on_disk(self, tmp_path):
        path = tmp_path / "mydive.bez"
        path.write_bytes(b"bez-bytes")
        return path

    def test_convert_writes_sibling_mcap(self, drone, mocker, bez_on_disk, capsys):
        convert = mocker.patch(
            "blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap", return_value=7
        )
        assert main(["logs", "convert", str(bez_on_disk)]) == 0
        convert.assert_called_once_with(bez_on_disk, bez_on_disk.parent / "mydive.mcap")
        assert "7 messages" in capsys.readouterr().out
        # Purely local: the Drone class must never be constructed.
        drone._drone_cls.assert_not_called()

    def test_convert_with_output_dir(self, drone, mocker, bez_on_disk, tmp_path):
        convert = mocker.patch(
            "blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap", return_value=7
        )
        out_dir = tmp_path / "converted"
        assert main(["logs", "convert", str(bez_on_disk), "-o", str(out_dir)]) == 0
        convert.assert_called_once_with(bez_on_disk, out_dir / "mydive.mcap")
        assert out_dir.is_dir()

    def test_convert_multiple_files(self, drone, mocker, tmp_path):
        convert = mocker.patch(
            "blueye.sdk.cli.commands.logs.mcap.convert_bez_to_mcap", return_value=1
        )
        files = []
        for name in ("a.bez", "b.bez"):
            path = tmp_path / name
            path.write_bytes(b"x")
            files.append(str(path))
        assert main(["logs", "convert", *files]) == 0
        assert convert.call_count == 2

    def test_convert_missing_file_errors(self, drone, tmp_path, capsys):
        assert main(["logs", "convert", str(tmp_path / "nope.bez")]) == 1
        assert "No such file" in capsys.readouterr().err

    def test_convert_missing_dependency_guidance(self, drone, mocker, bez_on_disk, capsys):
        def fake_missing(names):
            return [name for name in names if name == "mcap_protobuf"]

        mocker.patch("blueye.sdk.cli.deps.missing", side_effect=fake_missing)
        assert main(["logs", "convert", str(bez_on_disk)]) == 1
        assert "blueye.sdk[cli]" in capsys.readouterr().out


class TestSearchFilterEnabled:
    def test_questionary_checkbox_gets_search_filter(self, mocker):
        from blueye.sdk.cli.prompts import QuestionaryPrompter

        checkbox = mocker.patch("questionary.checkbox")
        checkbox.return_value.ask.return_value = []
        # The binding rework runs on the real prompt object; not exercisable on a Mock.
        scope = mocker.patch("blueye.sdk.cli.prompts._scope_bulk_bindings_to_filter")
        QuestionaryPrompter().checkbox("Pick:", ["a", "b"], "--flag")
        assert checkbox.call_args.kwargs["use_search_filter"] is True
        scope.assert_called_once_with(checkbox.return_value)
