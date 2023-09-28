import blueye.protocol as bp
from google.protobuf.any_pb2 import Any

import blueye.sdk


def test_documentation_opener(mocker):
    mocked_webbrowser_open = mocker.patch("webbrowser.open", autospec=True)
    import os

    blueye.sdk.__file__ = os.path.abspath("/root/blueye/sdk/__init__.py")

    blueye.sdk.open_local_documentation()

    mocked_webbrowser_open.assert_called_with(os.path.abspath("/root/blueye.sdk_docs/index.html"))


def test_deserialize_any_to_message():
    message = bp.DepthTel(depth={"value": 1.0})
    message_serialized = bp.DepthTel.serialize(message)
    any_message = Any(
        type_url="type.googleapis.com/blueye.protocol.DepthTel", value=message_serialized
    )
    expected_message = blueye.sdk.utils.deserialize_any_to_message(any_message)
    assert expected_message[0] == bp.DepthTel
    assert expected_message[1] == message
