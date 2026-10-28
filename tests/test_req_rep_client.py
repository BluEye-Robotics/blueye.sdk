import blueye.protocol as bp
import pytest

import blueye.sdk


@pytest.mark.parametrize("message", [bp.DepthTel, "blueye.protocol.DepthTel"])
def test_parse_to_type(message):
    assert blueye.sdk.connection.ReqRepClient._parse_type_to_string(message) == "DepthTel"


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
