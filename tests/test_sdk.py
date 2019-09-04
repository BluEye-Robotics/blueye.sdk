import pytest
from time import sleep


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


class TestLights:
    def test_lights_returns_value(self, mocked_pioneer):
        mocked_pioneer._stateWatcher.general_state = {
            "lights_upper": 0}
        assert mocked_pioneer.lights == 0
