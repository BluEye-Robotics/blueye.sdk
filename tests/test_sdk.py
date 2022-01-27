from time import time
from unittest.mock import PropertyMock

import blueye.sdk
import pytest
import requests
from blueye.sdk import Drone
from freezegun import freeze_time


class TestLights:
    def test_lights_returns_value(self, mocked_drone):
        mocked_drone._state_watcher._general_state = {"lights_upper": 0}
        mocked_drone._state_watcher._general_state_received.set()
        assert mocked_drone.lights == 0


class TestPose:
    @pytest.mark.parametrize("old_angle, new_angle", [(0, 0), (180, 180), (-180, 180), (-1, 359)])
    def test_angle_conversion(self, mocked_drone, old_angle, new_angle):
        mocked_drone._state_watcher._general_state = {
            "roll": old_angle,
            "pitch": old_angle,
            "yaw": old_angle,
        }
        mocked_drone._state_watcher._general_state_received.set()
        pose = mocked_drone.pose
        assert pose["roll"] == new_angle
        assert pose["pitch"] == new_angle
        assert pose["yaw"] == new_angle


class TestSlaveMode:
    def test_warning_is_raised(self, mocker, mocked_slave_drone):
        mocked_warn = mocker.patch("warnings.warn", autospec=True)

        # Call function that requires tcp connection
        mocked_slave_drone.lights = 0

        mocked_warn.assert_called_once()


def test_documentation_opener(mocker):
    mocked_webbrowser_open = mocker.patch("webbrowser.open", autospec=True)
    import os

    blueye.sdk.__file__ = os.path.abspath("/root/blueye/sdk/__init__.py")

    blueye.sdk.open_local_documentation()

    mocked_webbrowser_open.assert_called_with(os.path.abspath("/root/blueye.sdk_docs/README.html"))


def test_feature_list(mocked_drone):
    mocked_drone._update_drone_info()
    assert mocked_drone.features == ["lasers", "harpoon"]


def test_feature_list_is_empty_on_old_versions(mocked_drone, requests_mock):
    import json

    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye Pioneer Underwater Drone",
        "model_name": "Blueye Pioneer",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP123456",
        "sw_version": "1.3.2-rocko-master",
    }
    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(dummy_drone_info).encode(),
    )
    mocked_drone._update_drone_info()
    assert mocked_drone.features == []


def test_software_version(mocked_drone):
    mocked_drone._update_drone_info()
    assert mocked_drone.software_version == "1.4.7-warrior-master"
    assert mocked_drone.software_version_short == "1.4.7"


def test_verify_sw_version_raises_connection_error_when_not_connected(mocked_drone: Drone, mocker):
    mocker.patch(
        "blueye.sdk.Drone.connection_established", new_callable=PropertyMock, return_value=False
    )
    with pytest.raises(ConnectionError):
        mocked_drone._verify_required_blunux_version("1.4.7")


def test_depth_reading(mocked_drone):
    depth = 10000
    mocked_drone._state_watcher._general_state = {"depth": depth}
    mocked_drone._state_watcher._general_state_received.set()
    assert mocked_drone.depth == depth


def test_error_flags(mocked_drone):
    error_flags = 64
    mocked_drone._state_watcher._general_state = {"error_flags": error_flags}
    mocked_drone._state_watcher._general_state_received.set()
    assert mocked_drone.error_flags == error_flags


def test_timeout_general_state(mocked_drone: Drone):
    mocked_drone._state_watcher._udp_timeout = 0.001
    with pytest.raises(TimeoutError):
        mocked_drone._state_watcher.general_state


def test_timeout_calibration_state(mocked_drone: Drone):
    mocked_drone._state_watcher._udp_timeout = 0.001
    with pytest.raises(TimeoutError):
        mocked_drone._state_watcher.calibration_state


def test_battery_state_of_charge_reading(mocked_drone):
    SoC = 77
    mocked_drone._state_watcher._general_state = {"battery_state_of_charge_rel": SoC}
    mocked_drone._state_watcher._general_state_received.set()
    assert mocked_drone.battery_state_of_charge == SoC


@pytest.mark.parametrize("version", ["1.4.7", "1.4.8", "1.5.0", "2.0.0"])
def test_still_picture_works_with_new_drone_version(mocked_drone, version):
    mocked_drone.software_version_short = version
    mocked_drone.camera.take_picture()
    mocked_drone._tcp_client.take_still_picture.assert_called_once()
    mocked_drone._tcp_client.reset_mock()


@pytest.mark.parametrize(
    "exception",
    [
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError,
    ],
)
def test_update_drone_info_raises_ConnectionError_when_not_connected(
    requests_mock, mocked_drone, exception
):

    requests_mock.get("http://192.168.1.101/diagnostics/drone_info", exc=exception)
    with pytest.raises(ConnectionError):
        mocked_drone._update_drone_info()


def test_wait_for_udp_com_raises_ConnectionError_on_timeout(mocker):
    import socket

    mocked_udp = mocker.patch("blueye.sdk.drone.UdpClient", autospec=True).return_value

    mocked_udp.attach_mock(mocker.patch("blueye.sdk.drone.socket.socket", autospec=True), "_sock")
    mocked_udp.get_data_dict.side_effect = socket.timeout
    with pytest.raises(ConnectionError):
        blueye.sdk.Drone._wait_for_udp_communication(0.001)


def test_connect_ignores_repeated_starts_on_watchdog_thread(mocked_drone):
    mocked_drone.disconnect()
    assert mocked_drone.connection_established is False
    mocked_drone._tcp_client.start.side_effect = RuntimeError
    mocked_drone.connect(1)
    assert mocked_drone.connection_established is True


def test_active_video_streams_fails_on_old_versions(mocked_drone):
    with pytest.raises(RuntimeError):
        _ = mocked_drone.active_video_streams


@pytest.mark.parametrize("mocked_drone", ["1.5.33"], indirect=True)
@pytest.mark.parametrize(
    "debug_flag, expected_connections",
    [
        (0x0000000000000000, 0),
        (0x0000000100000000, 1),
        (0x000000AB00000000, 171),
        (0x12345645789ABCDE, 69),
    ],
)
def test_active_video_streams_return_correct_number(
    mocked_drone: Drone, debug_flag, expected_connections
):
    mocked_drone._state_watcher._general_state = {"debug_flags": debug_flag}
    mocked_drone._state_watcher._general_state_received.set()
    assert mocked_drone.active_video_streams == expected_connections


class TestTilt:
    @pytest.mark.parametrize("version", ["0.1.2", "1.2.3"])
    def test_tilt_fails_on_old_version(self, mocked_drone, version):
        mocked_drone.software_version_short = version
        mocked_drone.features = ["tilt"]
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_speed(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.angle

    def test_tilt_fails_on_drone_without_tilt(self, mocked_drone: Drone):
        mocked_drone.features = []
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_speed(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.angle
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.stabilization_enabled
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.toggle_stabilization()

    @pytest.mark.parametrize(
        "thruster_setpoints, tilt_speed",
        [
            ((0, 0, 0, 0), 0),
            ((1, 1, 1, 1), 1),
            ((-1, -1, -1, -1), -1),
            ((0.1, 0.2, 0.3, 0.4), 0.5),
        ],
    )
    def test_tilt_calls_motion_input_with_correct_arguments(
        self, mocked_drone, thruster_setpoints, tilt_speed
    ):
        mocked_drone.features = ["tilt"]
        mocked_drone.software_version_short = "1.5.33"
        mocked_drone.motion._current_thruster_setpoints = {
            "surge": thruster_setpoints[0],
            "sway": thruster_setpoints[1],
            "heave": thruster_setpoints[2],
            "yaw": thruster_setpoints[3],
        }
        mocked_drone.camera.tilt.set_speed(tilt_speed)
        mocked_drone._tcp_client.motion_input_tilt.assert_called_with(
            *thruster_setpoints, 0, 0, tilt_speed
        )

    @pytest.mark.parametrize(
        "debug_flags, expected_angle",
        [
            (0x0000440000000000, 34.0),
            (0x12344456789ABCDE, 34.0),
            (0x0000000000000000, 0.0),
            (0x12340056789ABCDE, 0.0),
            (0x0000BE0000000000, -33.0),
            (0x1234BE56789ABCDE, -33.0),
        ],
    )
    def test_tilt_returns_expected_angle(self, mocked_drone, debug_flags, expected_angle):
        mocked_drone.features = ["tilt"]
        mocked_drone.software_version_short = "1.5.33"
        mocked_drone._state_watcher._general_state = {"debug_flags": debug_flags}
        mocked_drone._state_watcher._general_state_received.set()
        assert mocked_drone.camera.tilt.angle == expected_angle

    @pytest.mark.parametrize(
        "debug_flags, expected_state",
        [
            (0x0000000000000100, True),
            (0x12344456789AFFDE, True),
            (0x0000000000000000, False),
            (0x12344456789A00DE, False),
            (0x12344456789AF0DE, False),
        ],
    )
    def test_tilt_stabilization_state(self, mocked_drone: Drone, debug_flags, expected_state):
        mocked_drone.features = ["tilt"]
        mocked_drone.software_version_short = "1.6.42"
        mocked_drone._state_watcher._general_state = {"debug_flags": debug_flags}
        mocked_drone._state_watcher._general_state_received.set()
        assert mocked_drone.camera.tilt.stabilization_enabled == expected_state

    def test_toggle_tilt_stabilization(self, mocked_drone: Drone):
        mocked_drone.features = ["tilt"]
        mocked_drone.software_version_short = "1.6.42"
        mocked_drone.camera.tilt.toggle_stabilization()
        assert mocked_drone._tcp_client.toggle_tilt_stabilization.call_count == 1


class TestConfig:
    def test_water_density_property_returns_correct_value(self, mocked_drone: Drone):
        mocked_drone.software_version_short = "1.5.33"
        mocked_drone.config._water_density = 1000
        assert mocked_drone.config.water_density == 1000

    @pytest.mark.parametrize("version", ["0.1.2", "1.2.3", "1.4.7"])
    def test_setting_density_fails_on_old_versions(self, mocked_drone: Drone, version):
        mocked_drone.software_version_short = version
        with pytest.raises(RuntimeError):
            mocked_drone.config.water_density = 1000

    @pytest.mark.parametrize("version", ["1.5.0", "1.6.2", "2.1.3"])
    def test_setting_density_works_on_new_versions(self, mocked_drone: Drone, version):
        mocked_drone.software_version_short = version
        old_value = mocked_drone.config.water_density
        new_value = old_value + 10
        mocked_drone.config.water_density = new_value
        assert mocked_drone.config.water_density == new_value
        mocked_drone._tcp_client.set_water_density.assert_called_once()

    def test_set_drone_time_is_called_on_connetion(self, mocked_drone: Drone):
        with freeze_time("2019-01-01"):
            expected_time = int(time())
            mocked_drone.connect()
            mocked_drone._tcp_client.set_system_time.assert_called_with(expected_time)


class TestMotion:
    def test_boost_getter_returns_expected_value(self, mocked_drone):
        mocked_drone.motion._current_boost_setpoints["boost"] = 1
        assert mocked_drone.motion.boost == 1

    def test_boost_setter_produces_correct_motion_input_arguments(self, mocked_drone):
        boost_gain = 0.5
        mocked_drone.motion.boost = boost_gain
        mocked_drone._tcp_client.motion_input.assert_called_with(0, 0, 0, 0, 0, boost_gain)

    def test_slow_getter_returns_expected_value(self, mocked_drone):
        mocked_drone.motion._current_boost_setpoints["slow"] = 1
        assert mocked_drone.motion.slow == 1

    def test_slow_setter_produces_correct_motion_input_arguments(self, mocked_drone):
        slow_gain = 0.3
        mocked_drone.motion.slow = slow_gain
        mocked_drone._tcp_client.motion_input.assert_called_with(0, 0, 0, 0, slow_gain, 0)
