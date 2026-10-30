import os
import warnings
import webbrowser
from typing import Optional, Tuple

import blueye.protocol as bp
import google.protobuf.empty_pb2 as empty_pb2
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
    data descriptor (it defines `__set__`) so that assignments to read-only deprecated properties
    raise an AttributeError instead of silently shadowing the descriptor with an instance attribute.
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


class UnknownMessageTypeError(ValueError):
    """The type URL of an Any message names a type this SDK does not know

    The drone logs and publishes every message type its firmware knows, so a newer drone
    can produce types that an older blueye.protocol package has no class for.
    """

    def __init__(self, type_url: str):
        super().__init__(f"Unknown message type {type_url}")
        self.type_url = type_url


def deserialize_any_to_message(msg: Any) -> Tuple[type, proto.message.Message]:
    """Deserialize a protobuf Any message to a concrete message type.

    Args:
        msg (Any): The Any message to deserialize. Needs to be a message defined in the
                   blueye.protocol package, a well-known wrapper type (FloatValue, Int32Value,
                   etc) from google.protobuf.wrappers_pb2, or google.protobuf.Empty.

    Returns:
        A tuple with the message type and the deserialized message. blueye.protocol types
        come back as proto-plus messages, the google.protobuf types as plain protobuf messages.

    Raises:
        UnknownMessageTypeError: The type URL names a type this SDK does not have a class for.
    """
    type_url = msg.type_url
    google_prefix = "type.googleapis.com/google.protobuf."
    blueye_prefix = "type.googleapis.com/blueye.protocol."
    if type_url == google_prefix + "Empty":
        return (empty_pb2.Empty, empty_pb2.Empty.FromString(msg.value))
    if type_url.startswith(google_prefix):
        payload_type = getattr(wrappers, type_url[len(google_prefix) :], None)
        if payload_type is None:
            raise UnknownMessageTypeError(type_url)
        return (payload_type, payload_type.FromString(msg.value))
    if type_url.startswith(blueye_prefix):
        payload_type = getattr(bp, type_url[len(blueye_prefix) :], None)
        if payload_type is not None:
            return (payload_type, payload_type.deserialize(msg.value))
    raise UnknownMessageTypeError(type_url)


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
