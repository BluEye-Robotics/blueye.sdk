from types import SimpleNamespace

import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.mark.parametrize("message", [bp.DepthTel, "blueye.protocol.DepthTel"])
def test_parse_to_type(message):
    assert blueye.sdk.connection.ReqRepClient._parse_type_to_string(message) == "DepthTel"


def test_stop_ends_the_thread_while_waiting_for_a_reply():
    """A drone that never answers must not keep the thread, and its socket, alive after stop()."""
    # TEST-NET-1 (RFC 5737), so nothing ever answers
    client = blueye.sdk.connection.ReqRepClient(SimpleNamespace(_ip="192.0.2.1"))
    client.start()
    with pytest.raises(bp.exceptions.ResponseTimeout):
        client.ping(timeout=0.2)
    client.stop()
    client.join(timeout=1)
    assert not client.is_alive()
    assert client._socket.closed
