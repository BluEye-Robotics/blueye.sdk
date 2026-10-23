import blueye.protocol as bp
from google.protobuf.any_pb2 import Any

import blueye.sdk
import pytest


def test_documentation_opener(mocker):
    mocked_webbrowser_open = mocker.patch("webbrowser.open", autospec=True)
    import os

    blueye.sdk.__file__ = os.path.abspath("/root/blueye/sdk/__init__.py")

    blueye.sdk.open_local_documentation()

    mocked_webbrowser_open.assert_called_with(os.path.abspath("/root/blueye.sdk_docs/index.html"))


def test_deserialize_any_to_message_empty():
    from google.protobuf.empty_pb2 import Empty

    any_message = Any(type_url="type.googleapis.com/google.protobuf.Empty", value=b"")
    payload_type, payload = blueye.sdk.utils.deserialize_any_to_message(any_message)
    assert payload_type is Empty
    assert payload == Empty()


def test_deserialize_any_to_message_wrapper():
    from google.protobuf.wrappers_pb2 import FloatValue

    any_message = Any(
        type_url="type.googleapis.com/google.protobuf.FloatValue",
        value=FloatValue(value=2.5).SerializeToString(),
    )
    payload_type, payload = blueye.sdk.utils.deserialize_any_to_message(any_message)
    assert payload_type is FloatValue
    assert payload.value == 2.5


@pytest.mark.parametrize(
    "type_url",
    [
        "type.googleapis.com/blueye.protocol.FutureTel",
        "type.googleapis.com/google.protobuf.FutureValue",
        "type.googleapis.com/other.Thing",
        "",
    ],
)
def test_deserialize_any_to_message_unknown_type_raises(type_url):
    any_message = Any(type_url=type_url, value=b"\x08\x01")
    with pytest.raises(blueye.sdk.utils.UnknownMessageTypeError) as excinfo:
        blueye.sdk.utils.deserialize_any_to_message(any_message)
    assert excinfo.value.type_url == type_url
    assert type_url in str(excinfo.value)
    assert isinstance(excinfo.value, ValueError)


def test_deserialize_any_to_message():
    message = bp.DepthTel(depth={"value": 1.0})
    message_serialized = bp.DepthTel.serialize(message)
    any_message = Any(
        type_url="type.googleapis.com/blueye.protocol.DepthTel", value=message_serialized
    )
    expected_message = blueye.sdk.utils.deserialize_any_to_message(any_message)
    assert expected_message[0] == bp.DepthTel
    assert expected_message[1] == message
