import os
import webbrowser
from typing import Tuple

import blueye.protocol as bp
import proto
from google.protobuf.any_pb2 import Any

import blueye.sdk


def open_local_documentation():
    """Open a pre-built local version of the SDK documentation

    Useful when you are connected to the drone wifi, and don't have access to the online version.
    """
    sdk_path = os.path.dirname(blueye.sdk.__file__)

    # The documentation is located next to the top-level package so we move up a couple of levels
    documentation_path = os.path.abspath(sdk_path + "/../../blueye.sdk_docs/README.html")

    webbrowser.open(documentation_path)


def deserialize_any_to_message(msg: Any) -> Tuple[proto.message.MessageMeta, proto.message.Message]:
    """Deserialize a protobuf Any message to a concrete message type

    *Arguments*:

    * msg: The Any message to deserialize. Needs to be a message defined in the blueye.protocol
           package.

    *Returns*:

    * A tuple with the metatype and the deserialized message
    """
    payload_msg_name = msg.type_url.replace("type.googleapis.com/blueye.protocol.", "")
    payload_type = bp.__getattribute__(payload_msg_name)
    payload_msg_deserialized = payload_type.deserialize(msg.value)
    return (payload_type, payload_msg_deserialized)
