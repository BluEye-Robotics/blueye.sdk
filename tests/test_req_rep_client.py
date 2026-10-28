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


@pytest.mark.parametrize(
    "method, request_type",
    [
        ("set_telemetry_msg_publish_frequency", bp.SetPubFrequencyReq),
        ("set_telemetry_msg_log_frequency", bp.SetLogFrequencyReq),
    ],
)
def test_frequency_requests_carry_message_name_and_frequency(mocker, method, request_type):
    client = blueye.sdk.connection.ReqRepClient.__new__(blueye.sdk.connection.ReqRepClient)
    send = mocker.patch.object(client, "_send_request_get_response")

    getattr(client, method)(bp.Imu1Tel, 50)

    request = send.call_args.args[0]
    assert isinstance(request, request_type)
    assert request.message_type == "Imu1Tel"
    assert request.frequency == 50
