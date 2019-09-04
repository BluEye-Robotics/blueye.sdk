import pytest


@pytest.fixture
def mocked_clients(mocker):
    mocker.patch("blueye.protocol.UdpClient", autospec=True)
    mocker.patch("blueye.protocol.TcpClient", autospec=True)


@pytest.fixture
def mocked_pioneer(mocked_clients):
    from blueye.sdk import Pioneer
    return Pioneer(autoConnect=False)


class TestLights:
    def test_lights_returns_value(self, mocked_pioneer):
        mocked_pioneer._stateWatcher.general_state = {
            "lights_upper": 0}
        assert mocked_pioneer.lights == 0
