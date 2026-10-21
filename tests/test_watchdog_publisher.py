import blueye.protocol as bp
import pytest

from blueye.sdk.connection import WatchdogPublisher


@pytest.fixture
def watchdog(mocker, mocked_drone_not_connected):
    context = mocker.MagicMock()
    return WatchdogPublisher(mocked_drone_not_connected, context=context)


def test_no_pet_before_the_drone_has_handed_out_a_client_id(watchdog):
    assert watchdog._parent_drone.client_id is None
    watchdog.pet_watchdog(duration=1)
    watchdog._socket.send_multipart.assert_not_called()


def test_pet_carries_the_client_id(watchdog):
    watchdog._parent_drone.client_id = 3
    watchdog.pet_watchdog(duration=5)
    (frames,), _ = watchdog._socket.send_multipart.call_args
    assert frames[0] == b"blueye.protocol.WatchdogCtrl"
    msg = bp.WatchdogCtrl.deserialize(frames[1])
    assert msg.client_id == 3
    assert msg.connection_duration.value == 5
