import os
import webbrowser
from typing import Tuple

import blueye.protocol as bp
import google.protobuf.wrappers_pb2 as wrappers
import proto
from google.protobuf.any_pb2 import Any
from google.protobuf.wrappers_pb2 import (
    BoolValue,
    BytesValue,
    DoubleValue,
    FloatValue,
    Int32Value,
    Int64Value,
    StringValue,
    UInt32Value,
    UInt64Value,
)

import blueye.sdk


def open_local_documentation():
    """Open a pre-built local version of the SDK documentation

    Useful when you are connected to the drone wifi, and don't have access to the online version.
    """
    sdk_path = os.path.dirname(blueye.sdk.__file__)

    # The documentation is located next to the top-level package so we move up a couple of levels
    documentation_path = os.path.abspath(sdk_path + "/../../blueye.sdk_docs/index.html")

    webbrowser.open(documentation_path)


def deserialize_any_to_message(msg: Any) -> Tuple[proto.message.MessageMeta, proto.message.Message]:
    """Deserialize a protobuf Any message to a concrete message type.

    Args:
        msg (Any): The Any message to deserialize. Needs to be a message defined in the
                   blueye.protocol package or a well-known-type (FloatValue, Int32Value, etc) from
                   google.protobuf.wrappers_pb2

    Returns:
        A tuple with the message type and the deserialized message.
    """
    if msg.type_url.startswith("type.googleapis.com/google.protobuf"):
        payload_msg_name = msg.type_url.replace("type.googleapis.com/google.protobuf.", "")
        payload_type = wrappers.__getattribute__(payload_msg_name)
        payload_msg_deserialized = payload_type.FromString(msg.value)
        return (payload_type, payload_msg_deserialized)

    payload_msg_name = msg.type_url.replace("type.googleapis.com/blueye.protocol.", "")
    payload_type = bp.__getattribute__(payload_msg_name)
    payload_msg_deserialized = payload_type.deserialize(msg.value)
    return (payload_type, payload_msg_deserialized)


def is_scalar_type(msg: proto.message.Message) -> bool:
    """Check if a message is a scalar type

    Args:
        msg (proto.message.Message): The message to check

    Returns:
        True if the message is a scalar type, False otherwise
    """

    scalar_types = (
        FloatValue,
        Int32Value,
        Int64Value,
        UInt32Value,
        UInt64Value,
        DoubleValue,
        BoolValue,
        StringValue,
        BytesValue,
    )
    return isinstance(msg, scalar_types)
