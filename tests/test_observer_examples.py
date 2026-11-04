"""Read-only example connections must not take or inherit control."""

import ast
import runpy
from pathlib import Path

import blueye.protocol as bp
import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize(
    "filename",
    [
        "print_depth.py",
        "print_imu.py",
        "print_status.py",
        "profiler.py",
        "parse_log_to_dataframe.py",
        "nmea_publisher.py",
        "nmea_heading_publisher.py",
    ],
)
def test_drone_connections_are_observers_in_context_managers(filename):
    # Includes optional-dependency examples without importing pandas or terminal/serial drivers.
    tree = ast.parse((EXAMPLES / filename).read_text())
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "Drone"
    ]
    assert calls
    contexts = [
        item.context_expr
        for node in ast.walk(tree)
        if isinstance(node, ast.With)
        for item in node.items
    ]
    for call in calls:
        assert call in contexts
        assert any(
            keyword.arg == "connect_as_observer"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in call.keywords
        )


@pytest.mark.parametrize("filename", ["print_depth.py", "print_imu.py", "profiler.py"])
def test_interrupt_exits_the_drone_context(filename, mocker):
    drone_class = mocker.patch("blueye.sdk.Drone")
    drone = drone_class.return_value
    drone.__enter__.return_value = drone
    mocker.patch("time.sleep", side_effect=KeyboardInterrupt)
    with pytest.raises(KeyboardInterrupt):
        runpy.run_path(str(EXAMPLES / filename), run_name="__main__")
    drone_class.assert_called_once_with(connect_as_observer=True)
    assert drone.__exit__.call_args.args[0] is KeyboardInterrupt
    if filename == "print_depth.py":
        assert drone.telemetry.set_msg_publish_frequency.call_args_list == [
            mocker.call(bp.DepthTel, 5),
            mocker.call(bp.DepthTel, 10),
        ]
        drone.telemetry.remove_msg_callback.assert_called_once_with(
            drone.telemetry.add_msg_callback.return_value
        )
    else:
        drone.telemetry.set_msg_publish_frequency.assert_not_called()


def test_profiler_import_has_no_connection_and_handles_no_samples(mocker, capsys):
    drone_class = mocker.patch("blueye.sdk.Drone")
    module = runpy.run_path(str(EXAMPLES / "profiler.py"))
    drone_class.assert_not_called()
    module["print_stats"]()
    assert capsys.readouterr().out == ""


def test_profiler_handles_first_sample_and_empty_payloads(mocker, capsys):
    module = runpy.run_path(str(EXAMPLES / "profiler.py"))
    clock = mocker.patch("time.monotonic", return_value=1)
    module["parse_message"]("EmptyTel", b"")
    module["print_stats"]()
    assert capsys.readouterr().out == ""
    clock.return_value = 2
    module["parse_message"]("EmptyTel", b"")
    module["print_stats"]()
    assert "bytes per s: 0" in capsys.readouterr().out
