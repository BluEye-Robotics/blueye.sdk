import pytest


@pytest.fixture
def mocked_clients(mocker):
    mocker.patch("blueye.protocol.UdpClient", autospec=True)
    mocker.patch("blueye.protocol.TcpClient", autospec=True)


@pytest.fixture
def mocked_pioneer(mocked_clients):
    from blueye.sdk import Pioneer
    return Pioneer()


class TestLights:
    def test_lights_returns_tuple(self, mocked_pioneer):
        mocked_pioneer._state.general_state = {
            "lights_upper": 0, "lights_lower": 0}
        assert mocked_pioneer.lights == (0, 0)

    def test_tuple_unpacking_fails_with_one_value(self, mocked_pioneer):
        with pytest.raises(TypeError):
            mocked_pioneer.lights = 1

    def test_tuple_unpacking_fails_with_more_than_two_values(self,
                                                             mocked_pioneer):
        with pytest.raises(TypeError):
            mocked_pioneer.lights = 1, 2, 3
