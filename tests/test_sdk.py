from time import time
from unittest.mock import Mock

import blueye.sdk
import pytest
import requests


@pytest.fixture(scope="class")
def pioneer():
    from blueye.sdk import Pioneer

    return Pioneer()


@pytest.fixture
def mocked_requests(requests_mock):
    import json

    dummy_drone_info = {
        "commit_id_csys": "299238949a",
        "features": "lasers,harpoon",
        "hardware_id": "ea9ac92e1817a1d4",
        "manufacturer": "Blueye Robotics",
        "model_description": "Blueye Pioneer Underwater Drone",
        "model_name": "Blueye Pioneer",
        "model_url": "https://www.blueyerobotics.com",
        "operating_system": "blunux",
        "serial_number": "BYEDP123456",
        "sw_version": "1.4.7-warrior-master",
    }
    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info",
        content=json.dumps(dummy_drone_info).encode(),
    )

    dummy_logs = json.dumps(
        [
            {
                "maxdepth": 1000,
                "name": "log1.csv",
                "timestamp": "2019-01-01T00:00:00.000000",
                "binsize": 1024,
            },
            {
                "maxdepth": 2000,
                "name": "log2.csv",
                "timestamp": "2019-01-02T00:00:00.000000",
                "binsize": 2048,
            },
        ]
    )
    requests_mock.get(f"http://192.168.1.101/logcsv", content=str.encode(dummy_logs))


@pytest.fixture
def mocked_pioneer(mocker, mocked_requests):
    mocker.patch("blueye.sdk.pioneer.UdpClient", autospec=True)
    mocker.patch("blueye.sdk.pioneer.TcpClient", create=True)
    p = blueye.sdk.Pioneer(autoConnect=False)
    p._wait_for_udp_communication = Mock()
    # Mocking out the run function to avoid blowing up the stack when the thread continuously calls
    # the get_data_dict function (which won't block since it's mocked).
    p._state_watcher.run = Mock()
    p.connect()
    return p


@pytest.fixture
def mocked_slave_pioneer(mocker, mocked_requests):
    mocker.patch("blueye.sdk.pioneer.UdpClient", autospec=True)
    mocker.patch("blueye.sdk.pioneer.TcpClient", create=True)
    p = blueye.sdk.Pioneer(autoConnect=False, slaveModeEnabled=True)
    p._wait_for_udp_communication = Mock()
    # Mocking out the run function to avoid blowing up the stack when the thread continuously calls
    # the get_data_dict function (which won't block since it's mocked).
    p._state_watcher.run = Mock()
    p.connect()
    return p


def polling_assert_with_timeout(cls, property_name, value_to_wait_for, timeout):
    """Waits for a property to change on the given class"""
    start_time = time()
    property_getter = type(cls).__dict__[property_name].__get__
    value = property_getter(cls)
    while value != value_to_wait_for:
        if time() - start_time > timeout:
            assert value == value_to_wait_for
        value = property_getter(cls)


@pytest.mark.connected_to_drone
class TestFunctionsWhenConnectedToDrone:
    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_heading(self, pioneer, new_state):
        pioneer.motion.auto_heading_active = new_state
        polling_assert_with_timeout(pioneer.motion, "auto_heading_active", new_state, 3)

    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_depth(self, pioneer, new_state):
        pioneer.motion.auto_depth_active = new_state
        polling_assert_with_timeout(pioneer.motion, "auto_depth_active", new_state, 3)

    def test_run_ping(self, pioneer):
        pioneer.ping()

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_recording(self, pioneer):
        test_read_property = pioneer.camera.is_recording
        pioneer.camera.is_recording = True
        polling_assert_with_timeout(pioneer.camera, "is_recording", True, 1)
        pioneer.camera.is_recording = False
        polling_assert_with_timeout(pioneer.camera, "is_recording", False, 1)

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_record_time(self, pioneer):
        test_read_property = pioneer.camera.record_time
        pioneer.camera.is_recording = True
        polling_assert_with_timeout(pioneer.camera, "record_time", 1, 3)

    def test_camera_bitrate(self, pioneer):
        test_read_parameter = pioneer.camera.bitrate
        pioneer.camera.bitrate = 2000000
        polling_assert_with_timeout(pioneer.camera, "bitrate", 2000000, 1)
        pioneer.camera.bitrate = 3000000
        polling_assert_with_timeout(pioneer.camera, "bitrate", 3000000, 1)

    def test_camera_exposure(self, pioneer):
        test_read_parameter = pioneer.camera.exposure
        pioneer.camera.exposure = 1200
        polling_assert_with_timeout(pioneer.camera, "exposure", 1200, 1)
        pioneer.camera.exposure = 1400
        polling_assert_with_timeout(pioneer.camera, "exposure", 1400, 1)

    def test_camera_whitebalance(self, pioneer):
        test_read_parameter = pioneer.camera.whitebalance
        pioneer.camera.whitebalance = 3200
        polling_assert_with_timeout(pioneer.camera, "whitebalance", 3200, 1)
        pioneer.camera.whitebalance = 3400
        polling_assert_with_timeout(pioneer.camera, "whitebalance", 3400, 1)

    def test_camera_hue(self, pioneer):
        test_read_parameter = pioneer.camera.hue
        pioneer.camera.hue = 20
        polling_assert_with_timeout(pioneer.camera, "hue", 20, 1)
        pioneer.camera.hue = 30
        polling_assert_with_timeout(pioneer.camera, "hue", 30, 1)

    def test_camera_resolution(self, pioneer):
        test_read_parameter = pioneer.camera.resolution
        pioneer.camera.resolution = 480
        polling_assert_with_timeout(pioneer.camera, "resolution", 480, 1)
        pioneer.camera.resolution = 720
        polling_assert_with_timeout(pioneer.camera, "resolution", 720, 1)

    def test_camera_framerate(self, pioneer):
        test_read_parameter = pioneer.camera.framerate
        pioneer.camera.framerate = 25
        polling_assert_with_timeout(pioneer.camera, "framerate", 25, 1)
        pioneer.camera.framerate = 30
        polling_assert_with_timeout(pioneer.camera, "framerate", 30, 1)


class TestLights:
    def test_lights_returns_value(self, mocked_pioneer):
        mocked_pioneer._state_watcher._general_state = {"lights_upper": 0}
        assert mocked_pioneer.lights == 0


class TestPose:
    @pytest.mark.parametrize("old_angle, new_angle", [(0, 0), (180, 180), (-180, 180), (-1, 359)])
    def test_angle_conversion(self, mocked_pioneer, old_angle, new_angle):
        mocked_pioneer._state_watcher._general_state = {
            "roll": old_angle,
            "pitch": old_angle,
            "yaw": old_angle,
        }
        pose = mocked_pioneer.pose
        assert pose["roll"] == new_angle
        assert pose["pitch"] == new_angle
        assert pose["yaw"] == new_angle


class TestSlaveMode:
    def test_warning_is_raised(self, mocker, mocked_slave_pioneer):
        mocked_warn = mocker.patch("warnings.warn", autospec=True)

        # Call function that requires tcp connection
        mocked_slave_pioneer.lights = 0

        mocked_warn.assert_called_once()


def test_documentation_opener(mocker):
    mocked_webbrowser_open = mocker.patch("webbrowser.open", autospec=True)
    import os

    blueye.sdk.__file__ = os.path.abspath("/root/blueye/sdk/__init__.py")

    blueye.sdk.open_local_documentation()

    mocked_webbrowser_open.assert_called_with(os.path.abspath("/root/blueye.sdk_docs/README.html"))


def test_feature_list(mocked_pioneer):
    mocked_pioneer._update_drone_info()
    assert mocked_pioneer.features == ["lasers", "harpoon"]


def test_feature_list_is_empty_on_old_versions(mocked_pioneer, requests_mock):
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
    mocked_pioneer._update_drone_info()
    assert mocked_pioneer.features == []


def test_software_version(mocked_pioneer):
    mocked_pioneer._update_drone_info()
    assert mocked_pioneer.software_version == "1.4.7-warrior-master"
    assert mocked_pioneer.software_version_short == "1.4.7"


def test_depth_reading(mocked_pioneer):
    depth = 10000
    mocked_pioneer._state_watcher._general_state = {"depth": depth}
    assert mocked_pioneer.depth == depth


def test_battery_state_of_charge_reading(mocked_pioneer):
    SoC = 77
    mocked_pioneer._state_watcher._general_state = {"battery_state_of_charge_rel": SoC}
    assert mocked_pioneer.battery_state_of_charge == SoC


@pytest.mark.parametrize("version", ["1.4.7", "1.4.8", "1.5.0", "2.0.0"])
def test_still_picture_works_with_new_drone_version(mocked_pioneer, version):
    mocked_pioneer.software_version_short = version
    mocked_pioneer.camera.take_picture()
    mocked_pioneer._tcp_client.take_still_picture.assert_called_once()
    mocked_pioneer._tcp_client.reset_mock()


@pytest.mark.parametrize(
    "exception",
    [
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectionError,
    ],
)
def test_update_drone_info_raises_ConnectionError_when_not_connected(
    requests_mock, mocked_pioneer, exception
):

    requests_mock.get(
        "http://192.168.1.101/diagnostics/drone_info", exc=exception,
    )
    with pytest.raises(ConnectionError):
        mocked_pioneer._update_drone_info()


def test_wait_for_udp_com_raises_ConnectionError_on_timeout(mocker):
    import socket

    mocked_udp = mocker.patch("blueye.sdk.pioneer.UdpClient", autospec=True).return_value

    mocked_udp.attach_mock(mocker.patch("blueye.sdk.pioneer.socket.socket", autospec=True), "_sock")
    mocked_udp.get_data_dict.side_effect = socket.timeout
    with pytest.raises(ConnectionError):
        blueye.sdk.Pioneer._wait_for_udp_communication(1)


def test_establish_tcp_connection_raises_ConnectionError(mocked_pioneer):
    from blueye.protocol.exceptions import NoConnectionToDrone

    mocked_pioneer._tcp_client.connect.side_effect = NoConnectionToDrone("", "")
    with pytest.raises(ConnectionError):
        mocked_pioneer._establish_tcp_connection()


def test_establish_tcp_connection_ignores_RuntimeErrors(mocked_pioneer):
    mocked_pioneer.connection_established = False
    mocked_pioneer._tcp_client.start.side_effect = RuntimeError
    mocked_pioneer._establish_tcp_connection()
    assert mocked_pioneer.connection_established is True


@pytest.mark.parametrize("version", ["0.1.2", "1.2.3"])
def test_tilt_fails_on_old_version(mocked_pioneer, version):
    mocked_pioneer.software_version_short = version
    mocked_pioneer.features = ["tilt"]
    with pytest.raises(RuntimeError):
        mocked_pioneer.camera.tilt.set_speed(0)
        _ = mocked_pioneer.camera.tilt.angle


def test_tilt_fails_on_drone_without_tilt(mocked_pioneer):
    mocked_pioneer.features = []
    with pytest.raises(RuntimeError):
        mocked_pioneer.camera.tilt.set_speed(0)
        _ = mocked_pioneer.camera.tilt.angle


@pytest.mark.parametrize(
    "thruster_setpoints, tilt_speed",
    [((0, 0, 0, 0), 0), ((1, 1, 1, 1), 1), ((-1, -1, -1, -1), -1), ((0.1, 0.2, 0.3, 0.4), 0.5),],
)
def test_tilt_calls_motion_input_with_correct_arguments(
    mocked_pioneer, thruster_setpoints, tilt_speed
):
    mocked_pioneer.features = ["tilt"]
    mocked_pioneer.software_version_short = "1.5.0"
    mocked_pioneer.motion.current_thruster_setpoints = {
        "surge": thruster_setpoints[0],
        "sway": thruster_setpoints[1],
        "heave": thruster_setpoints[2],
        "yaw": thruster_setpoints[3],
    }
    mocked_pioneer.camera.tilt.set_speed(tilt_speed)
    mocked_pioneer._tcp_client.motion_input_tilt.assert_called_with(
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
def test_tilt_returns_expected_angle(mocked_pioneer, debug_flags, expected_angle):
    mocked_pioneer.features = ["tilt"]
    mocked_pioneer.software_version_short = "1.5.0"
    mocked_pioneer._state_watcher._general_state = {"debug_flags": debug_flags}
    assert mocked_pioneer.camera.tilt.angle == expected_angle
