from time import sleep, time

import pytest


@pytest.fixture(scope="class")
def pioneer():
    from blueye.sdk import Pioneer

    return Pioneer()


@pytest.fixture
def mocked_clients(mocker):
    mocker.patch("blueye.protocol.UdpClient", autospec=True)
    mocker.patch("blueye.protocol.TcpClient", autospec=True)


@pytest.fixture
def mocked_pioneer(mocked_clients):
    from blueye.sdk import Pioneer

    return Pioneer(autoConnect=False)


@pytest.fixture
def mocked_slave_pioneer(mocked_clients):
    from blueye.sdk import Pioneer

    return Pioneer(autoConnect=False, slaveModeEnabled=True)


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
    @pytest.mark.parametrize(
        "old_angle, new_angle", [(0, 0), (180, 180), (-180, 180), (-1, 359)]
    )
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
