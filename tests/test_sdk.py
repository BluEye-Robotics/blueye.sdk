import pytest
from time import sleep


@pytest.fixture(scope="class")
def pioneer():
    from blueye.sdk import Pioneer

    sleep(1)  # wait for to drone send first UDP message
    return Pioneer()


@pytest.fixture
def mocked_clients(mocker):
    mocker.patch("blueye.protocol.UdpClient", autospec=True)
    mocker.patch("blueye.protocol.TcpClient", autospec=True)


@pytest.fixture
def mocked_pioneer(mocked_clients):
    from blueye.sdk import Pioneer

    return Pioneer(autoConnect=False)


@pytest.mark.connected_to_drone
class TestFunctionsWhenConnectedToDrone:
    def test_auto_heading(self, pioneer):
        pioneer.auto_heading_active = True
        sleep(0.3)  # wait for new UDP message
        assert pioneer.auto_heading_active == True

    def test_auto_depth(self, pioneer):
        pioneer.auto_depth_active = True
        sleep(0.1)  # wait for new UDP message
        assert pioneer.auto_heading_active == True

    def test_run_ping(self, pioneer):
        pioneer.ping()

    @pytest.mark.skip(
        reason="a camera stream must have been run before camera recording is possible"
    )
    def test_camera_recording(self, pioneer):
        test_read_property = pioneer.camera.is_recording
        pioneer.camera.is_recording = True
        sleep(1)
        assert pioneer.camera.is_recording == True
        pioneer.camera.is_recording = False
        sleep(1)
        assert pioneer.camera.is_recording == False

    def test_camera_bitrate(self, pioneer):
        test_read_parameter = pioneer.camera.bitrate
        bitrate_value = 3000000
        pioneer.camera.bitrate = bitrate_value
        sleep(1)
        assert pioneer.camera.bitrate == bitrate_value

    def test_camera_exposure(self, pioneer):
        test_read_parameter = pioneer.camera.exposure
        exposure_value = 1200
        pioneer.camera.exposure = exposure_value
        sleep(1)
        assert pioneer.camera.exposure == exposure_value

    def test_camera_whitebalance(self, pioneer):
        test_read_parameter = pioneer.camera.whitebalance
        whitebalance_value = 3200
        pioneer.camera.whitebalance = whitebalance_value
        sleep(1)
        assert pioneer.camera.whitebalance == whitebalance_value

    def test_camera_hue(self, pioneer):
        test_read_parameter = pioneer.camera.hue
        hue_value = 20
        pioneer.camera.hue = hue_value
        sleep(1)
        assert pioneer.camera.hue == hue_value

    def test_camera_resolution(self, pioneer):
        test_read_parameter = pioneer.camera.resolution
        resolution_value = 480
        pioneer.camera.resolution = resolution_value
        assert pioneer.camera.resolution == resolution_value

    def test_camera_framerate(self, pioneer):
        test_read_parameter = pioneer.camera.framerate
        framerate_value = 25
        pioneer.camera.framerate = framerate_value
        assert pioneer.camera.framerate == framerate_value


class TestLights:
    def test_lights_returns_value(self, mocked_pioneer):
        mocked_pioneer._state_watcher._general_state = {"lights_upper": 0}
        assert mocked_pioneer.lights == 0
