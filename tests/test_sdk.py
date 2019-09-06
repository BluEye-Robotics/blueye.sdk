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
        sleep(0.1)  # wait for new UDP message
        assert(pioneer.auto_heading_active == True)

    def test_auto_depth(self, pioneer):
        pioneer.auto_depth_active = True
        sleep(0.1)  # wait for new UDP message
        assert(pioneer.auto_heading_active == True)

    def test_run_ping(self, pioneer):
        pioneer.ping()

    @pytest.mark.skip(reason="a camera stream must have been run before camera recording is possible")
    def test_camera_recording(self, pioneer):
        pioneer.camera.is_recording = True
        sleep(1)
        assert(pioneer.camera.is_recording == True)
        pioneer.camera.is_recording = False
        sleep(1)
        assert(pioneer.camera.is_recording == False)


class TestLights:
    def test_lights_returns_value(self, mocked_pioneer):
        mocked_pioneer._state_watcher.general_state = {
            "lights_upper": 0}
        assert mocked_pioneer.lights == 0
