from time import time
from unittest.mock import Mock

import pytest
import requests
from freezegun import freeze_time

import blueye.sdk
from blueye.sdk import Drone


@pytest.fixture(scope="class")
def real_drone():
    """Fixture that autoconnects to a drone

    Used for integration tests with physical hardware.
    """
    return Drone()


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
def mocked_TcpClient(mocker):
    """Fixture for mocking the TcpClient from blueye.protocol

    Note: This mock is passed create=True, which has the potential to be dangerous since it would
    allow you to test against methods that don't exist on the actual class. Due to the way methods
    are added to TcpClient (they are instantiated on runtime, depending on which version of the
    protocol is requested) mocking the class in the usual way would be quite cumbersome.
    """
    return mocker.patch("blueye.sdk.drone.TcpClient", create=True)


@pytest.fixture
def mocked_UdpClient(mocker):
    return mocker.patch("blueye.sdk.drone.UdpClient", autospec=True)


@pytest.fixture
def mocked_drone(mocker, mocked_TcpClient, mocked_UdpClient, mocked_requests):
    drone = blueye.sdk.Drone(autoConnect=False, udpTimeout=0.2)
    drone._wait_for_udp_communication = Mock()
    # Mocking out the run function to avoid blowing up the stack when the thread continuously calls
    # the get_data_dict function (which won't block since it's mocked).
    drone._state_watcher.run = Mock()
    drone.connect()
    return drone


@pytest.fixture
def mocked_slave_drone(mocker, mocked_TcpClient, mocked_UdpClient, mocked_requests):
    drone = blueye.sdk.Drone(autoConnect=False, slaveModeEnabled=True)
    drone._wait_for_udp_communication = Mock()
    # Mocking out the run function to avoid blowing up the stack when the thread continuously calls
    # the get_data_dict function (which won't block since it's mocked).
    drone._state_watcher.run = Mock()
    drone.connect()
    return drone


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
    def test_auto_heading(self, real_drone, new_state):
        real_drone.motion.auto_heading_active = new_state
        polling_assert_with_timeout(real_drone.motion, "auto_heading_active", new_state, 3)

    @pytest.mark.parametrize("new_state", [True, False])
    def test_auto_depth(self, real_drone, new_state):
        real_drone.motion.auto_depth_active = new_state
        polling_assert_with_timeout(real_drone.motion, "auto_depth_active", new_state, 3)

    def test_run_ping(self, real_drone):
        real_drone.ping()

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_recording(self, real_drone):
        test_read_property = real_drone.camera.is_recording
        real_drone.camera.is_recording = True
        polling_assert_with_timeout(real_drone.camera, "is_recording", True, 1)
        real_drone.camera.is_recording = False
        polling_assert_with_timeout(real_drone.camera, "is_recording", False, 1)

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_record_time(self, real_drone):
        test_read_property = real_drone.camera.record_time
        real_drone.camera.is_recording = True
        polling_assert_with_timeout(real_drone.camera, "record_time", 1, 3)

    def test_camera_bitrate(self, real_drone):
        test_read_parameter = real_drone.camera.bitrate
        real_drone.camera.bitrate = 2000000
        polling_assert_with_timeout(real_drone.camera, "bitrate", 2000000, 1)
        real_drone.camera.bitrate = 3000000
        polling_assert_with_timeout(real_drone.camera, "bitrate", 3000000, 1)

    def test_camera_exposure(self, real_drone):
        test_read_parameter = real_drone.camera.exposure
        real_drone.camera.exposure = 1200
        polling_assert_with_timeout(real_drone.camera, "exposure", 1200, 1)
        real_drone.camera.exposure = 1400
        polling_assert_with_timeout(real_drone.camera, "exposure", 1400, 1)

    def test_camera_whitebalance(self, real_drone):
        test_read_parameter = real_drone.camera.whitebalance
        real_drone.camera.whitebalance = 3200
        polling_assert_with_timeout(real_drone.camera, "whitebalance", 3200, 1)
        real_drone.camera.whitebalance = 3400
        polling_assert_with_timeout(real_drone.camera, "whitebalance", 3400, 1)

    def test_camera_hue(self, real_drone):
        test_read_parameter = real_drone.camera.hue
        real_drone.camera.hue = 20
        polling_assert_with_timeout(real_drone.camera, "hue", 20, 1)
        real_drone.camera.hue = 30
        polling_assert_with_timeout(real_drone.camera, "hue", 30, 1)

    def test_camera_resolution(self, real_drone):
        test_read_parameter = real_drone.camera.resolution
        real_drone.camera.resolution = 480
        polling_assert_with_timeout(real_drone.camera, "resolution", 480, 1)
        real_drone.camera.resolution = 720
        polling_assert_with_timeout(real_drone.camera, "resolution", 720, 1)

    def test_camera_framerate(self, real_drone):
        test_read_parameter = real_drone.camera.framerate
        real_drone.camera.framerate = 25
        polling_assert_with_timeout(real_drone.camera, "framerate", 25, 1)
        real_drone.camera.framerate = 30
        polling_assert_with_timeout(real_drone.camera, "framerate", 30, 1)


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


def test_timeout_general_state(mocked_drone):
    with pytest.raises(TimeoutError):
        mocked_drone._state_watcher.general_state


def test_timeout_calibration_state(mocked_drone):
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
        blueye.sdk.Drone._wait_for_udp_communication(1)


def test_connect_ignores_repeated_starts_on_watchdog_thread(mocked_drone):
    mocked_drone.disconnect()
    assert mocked_drone.connection_established is False
    mocked_drone._tcp_client.start.side_effect = RuntimeError
    mocked_drone.connect(1)
    assert mocked_drone.connection_established is True


def test_creating_Pioneer_object_raises_DeprecationWarning():
    from blueye.sdk import Pioneer

    with pytest.warns(DeprecationWarning):
        _ = Pioneer(autoConnect=False)


class TestTilt:
    @pytest.mark.parametrize("version", ["0.1.2", "1.2.3"])
    def test_tilt_fails_on_old_version(self, mocked_drone, version):
        mocked_drone.software_version_short = version
        mocked_drone.features = ["tilt"]
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_speed(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.angle

    def test_tilt_fails_on_drone_without_tilt(self, mocked_drone):
        mocked_drone.features = []
        with pytest.raises(RuntimeError):
            mocked_drone.camera.tilt.set_speed(0)
        with pytest.raises(RuntimeError):
            _ = mocked_drone.camera.tilt.angle

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
