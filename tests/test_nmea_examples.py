"""Exercise the example scripts without a drone or serial device."""

import importlib
import math
import socket
import sys
from pathlib import Path
from types import SimpleNamespace

import blueye.protocol as bp
import pytest
from freezegun import freeze_time


@pytest.fixture
def examples(monkeypatch, mocker):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "examples"))
    monkeypatch.setitem(
        sys.modules, "serial", SimpleNamespace(Serial=mocker.MagicMock(), SerialException=OSError)
    )
    names = ["nmea_utils", "nmea_publisher", "nmea_heading_publisher", "nmea_position_input"]
    modules = SimpleNamespace(**{name: importlib.import_module(name) for name in names})
    yield modules
    for name in names:
        sys.modules.pop(name, None)


def sentence_body(sentence):
    """Validate framing/checksum independently of the formatter."""
    assert sentence.startswith("$")
    assert sentence.endswith("\r\n")
    body, checksum = sentence[1:-2].split("*")
    expected = 0
    for byte in body.encode("ascii"):
        expected ^= byte
    assert checksum == f"{expected:02X}"
    return body


def test_known_checksum(examples):
    assert examples.nmea_utils.nmea_sentence("GPGLL,4916.45,N,12311.12,W,225444,A") == (
        "$GPGLL,4916.45,N,12311.12,W,225444,A*31\r\n"
    )


@pytest.mark.parametrize(
    "lat,lon,coordinates",
    [
        (63.5, 10.25, "6330.0000,N,01015.0000,E"),
        (-33.8568, -151.2153, "3351.4080,S,15112.9180,W"),
        (-33.8568, 151.2153, "3351.4080,S,15112.9180,E"),
        (33.8568, -151.2153, "3351.4080,N,15112.9180,W"),
        (0, 0, "0000.0000,N,00000.0000,E"),
        (90, 180, "9000.0000,N,18000.0000,E"),
        (-90, -180, "9000.0000,S,18000.0000,W"),
        (12.99999999, -179.99999999, "1300.0000,N,18000.0000,W"),
    ],
)
@pytest.mark.parametrize("valid,status", [(True, "A"), (False, "V")])
@freeze_time("2026-01-02 03:04:05.670000")
def test_gll_coordinates_and_validity(examples, lat, lon, coordinates, valid, status):
    sentence = examples.nmea_utils.nmea_gll(lat, lon, valid)
    assert sentence_body(sentence) == f"GPGLL,{coordinates},030405.67,{status}"


@pytest.mark.parametrize(
    "lat,lon",
    [
        (91, 0),
        (-91, 0),
        (0, 181),
        (0, -181),
        (math.nan, 0),
        (0, math.nan),
        (math.inf, 0),
        (0, -math.inf),
    ],
)
def test_gll_rejects_bad_coordinates(examples, lat, lon):
    with pytest.raises(ValueError):
        examples.nmea_utils.nmea_gll(lat, lon, True)


@pytest.mark.parametrize(
    "heading,expected",
    [
        (-180, "180.0"),
        (-1, "359.0"),
        (0, "0.0"),
        (360, "0.0"),
        (721, "1.0"),
        (359.99, "0.0"),
        (-0.01, "0.0"),
    ],
)
def test_hdt_wraps_after_rounding(examples, heading, expected):
    assert sentence_body(examples.nmea_utils.nmea_hdt(heading)) == f"IIHDT,{expected},T"


@pytest.mark.parametrize("heading", [math.nan, math.inf, -math.inf])
def test_hdt_skips_non_finite_values(examples, heading):
    assert examples.nmea_utils.nmea_hdt(heading) is None


@pytest.mark.parametrize("valid", [True, False])
def test_position_publisher_uses_output_port_and_validity(examples, mocker, valid):
    udp = mocker.Mock()
    msg = bp.PositionEstimateTel(
        position_estimate={
            "global_position": {"latitude": -33.5, "longitude": -151.25},
            "is_valid": valid,
        }
    )
    examples.nmea_publisher.callback_position_estimate("PositionEstimateTel", msg, udp)
    packet, address = udp.sendto.call_args.args
    assert address == ("192.168.1.255", 10111)
    assert sentence_body(packet.decode("ascii")).endswith(",A" if valid else ",V")


def test_position_publisher_skips_nan(examples, mocker):
    udp = mocker.Mock()
    msg = bp.PositionEstimateTel(position_estimate={"global_position": {"latitude": math.nan}})
    examples.nmea_publisher.callback_position_estimate("PositionEstimateTel", msg, udp)
    udp.sendto.assert_not_called()


def test_input_sends_each_valid_line_once_and_skips_bad_lines(examples, mocker, capsys):
    udp = mocker.Mock()
    examples.nmea_position_input.forward_positions(
        ["-33.5 151.25 A\n", "0 0 V\n", "bad\n", "1 2 yes\n", "nan 0 A\n"], udp, "127.0.0.1"
    )
    assert udp.sendto.call_count == 2
    for call, status in zip(udp.sendto.call_args_list, ("A", "V")):
        packet, address = call.args
        assert address == ("127.0.0.1", 10110)
        assert sentence_body(packet.decode("ascii")).endswith(f",{status}")
    assert capsys.readouterr().err.count("Skipping line") == 3


def test_input_loopback_datagram(examples, monkeypatch):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
        receiver.bind(("127.0.0.1", 0))
        receiver.settimeout(1)
        monkeypatch.setattr(
            examples.nmea_position_input, "NMEA_INPUT_PORT", receiver.getsockname()[1]
        )
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
            examples.nmea_position_input.forward_positions(["63.5 10.25 A"], sender, "127.0.0.1")
        packet, _ = receiver.recvfrom(1024)
    assert sentence_body(packet.decode("ascii")).startswith("GPGLL,6330.0000,N,01015.0000,E,")


def test_publisher_connects_as_observer_and_cleans_up(examples, mocker):
    module = examples.nmea_publisher
    drone_class = mocker.patch.object(module, "Drone")
    socket_class = mocker.patch.object(module.socket, "socket")
    mocker.patch.object(module.time, "sleep", side_effect=KeyboardInterrupt)
    module.main()
    drone_class.assert_called_once_with(connect_as_observer=True)
    drone_class.return_value.__exit__.assert_called_once()
    socket_class.return_value.__exit__.assert_called_once()
    drone_class.return_value.__enter__.return_value.telemetry.set_msg_publish_frequency.assert_not_called()


@pytest.mark.parametrize(
    "yaw,age,expected_writes", [(None, 0, 0), (-1, 0, 1), (math.nan, 0, 0), (90, 2, 0)]
)
def test_heading_waits_for_fresh_valid_data_and_cleans_up(
    examples, mocker, yaw, age, expected_writes
):
    module = examples.nmea_heading_publisher
    drone_class = mocker.patch.object(module, "Drone")
    drone = drone_class.return_value.__enter__.return_value
    mocker.patch.object(module.time, "monotonic", return_value=100)

    def register(*args):
        if yaw is not None:
            module.callback_attitude("AttitudeTel", bp.AttitudeTel(attitude={"yaw": yaw}))
            module.last_attitude_time -= age

    drone.telemetry.add_msg_callback.side_effect = register
    mocker.patch.object(module.time, "sleep", side_effect=KeyboardInterrupt)
    module.main()
    drone_class.assert_called_once_with(connect_as_observer=True)
    drone.telemetry.set_msg_publish_frequency.assert_not_called()
    port = module.serial.Serial.return_value.__enter__.return_value
    assert port.write.call_count == expected_writes
    if expected_writes:
        assert sentence_body(port.write.call_args.args[0].decode("ascii")) == "IIHDT,359.0,T"
    drone_class.return_value.__exit__.assert_called_once()
    module.serial.Serial.return_value.__exit__.assert_called_once()
