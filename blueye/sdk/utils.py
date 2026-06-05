import os
import warnings
import webbrowser
from typing import Optional, Tuple

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


class deprecated_property:
    """Property shim that warns and delegates to the new getter/setter methods.

    `fget`/`fset` are the *names* of the replacement methods on the owning class. This is always a
    data descriptor (it defines `__set__`) so that a typo'd assignment to a read-only property still
    raises an AttributeError instead of silently shadowing the descriptor with an instance attribute.
    """

    def __init__(self, fget: str, fset: Optional[str] = None, doc: Optional[str] = None):
        self.fget = fget
        self.fset = fset
        self.__doc__ = doc

    def __set_name__(self, owner, name):
        self.owner = owner.__name__
        self.name = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        warnings.warn(
            f"`{self.owner}.{self.name}` is deprecated and will be removed in the next major "
            f"version. Use `{self.owner}.{self.fget}()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(obj, self.fget)()

    def __set__(self, obj, value):
        if self.fset is None:
            raise AttributeError(f"can't set attribute `{self.name}`")
        warnings.warn(
            f"`{self.owner}.{self.name}` is deprecated and will be removed in the next major "
            f"version. Use `{self.owner}.{self.fset}()` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        getattr(obj, self.fset)(value)


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
